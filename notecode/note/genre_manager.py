"""genre_manager.py - CRUD operations for custom genres."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Mapping, Optional

from note.policy_engine import normalize_category_meta

GENRES_FILE = Path(__file__).resolve().parent / "custom_genres.json"


def _load_data() -> dict:
    """Load genres data from file, creating empty structure if not exists."""
    if not GENRES_FILE.exists():
        return {"genres": []}
    try:
        with GENRES_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if "genres" not in data:
                data["genres"] = []
            return data
    except (json.JSONDecodeError, IOError):
        return {"genres": []}


def _save_data(data: dict) -> None:
    """Save genres data to file."""
    with GENRES_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _generate_key(label: str) -> str:
    """Generate a URL-safe key from label."""
    # Remove non-alphanumeric chars (keep Japanese), replace spaces with underscore
    key = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", "_", label)
    key = re.sub(r"_+", "_", key).strip("_").lower()
    return key or "custom_genre"


def load_genres() -> List[dict]:
    """Load all custom genres."""
    data = _load_data()
    genres = data.get("genres", [])
    normalized: List[dict] = []
    for genre in genres:
        if not isinstance(genre, dict):
            continue
        item = dict(genre)
        item["meta"] = normalize_category_meta(item.get("meta"))
        normalized.append(item)
    return normalized


def get_genre(key: str) -> Optional[dict]:
    """Get a single genre by key."""
    genres = load_genres()
    for g in genres:
        if g.get("key") == key:
            return g
    return None


def save_genre(
    key: str,
    label: str,
    prompt: str,
    meta: Optional[Mapping[str, str]] = None,
) -> None:
    """Save a new genre or update existing one."""
    data = _load_data()
    genres = data.get("genres", [])
    normalized_meta = normalize_category_meta(meta)
    
    # Check if key already exists
    for i, g in enumerate(genres):
        if g.get("key") == key:
            genres[i] = {"key": key, "label": label, "prompt": prompt, "meta": normalized_meta}
            data["genres"] = genres
            _save_data(data)
            return
    
    # Add new genre
    genres.append({"key": key, "label": label, "prompt": prompt, "meta": normalized_meta})
    data["genres"] = genres
    _save_data(data)


def add_genre(label: str, prompt: str, meta: Optional[Mapping[str, str]] = None) -> str:
    """Add a new genre with auto-generated key. Returns the generated key."""
    base_key = _generate_key(label)
    key = base_key
    
    # Ensure unique key
    existing_keys = {g.get("key") for g in load_genres()}
    counter = 1
    while key in existing_keys:
        key = f"{base_key}_{counter}"
        counter += 1
    
    save_genre(key, label, prompt, meta=meta)
    return key


def update_genre(
    key: str,
    label: str,
    prompt: str,
    meta: Optional[Mapping[str, str]] = None,
) -> bool:
    """Update an existing genre. Returns True if found and updated."""
    data = _load_data()
    genres = data.get("genres", [])
    normalized_meta = normalize_category_meta(meta)
    
    for i, g in enumerate(genres):
        if g.get("key") == key:
            current = g if isinstance(g, dict) else {}
            merged_meta = current.get("meta") if meta is None else normalized_meta
            genres[i] = {
                "key": key,
                "label": label,
                "prompt": prompt,
                "meta": normalize_category_meta(merged_meta),
            }
            data["genres"] = genres
            _save_data(data)
            return True
    return False


def delete_genre(key: str) -> bool:
    """Delete a genre by key. Returns True if found and deleted."""
    data = _load_data()
    genres = data.get("genres", [])
    
    original_len = len(genres)
    genres = [g for g in genres if g.get("key") != key]
    
    if len(genres) < original_len:
        data["genres"] = genres
        _save_data(data)
        return True
    return False


def get_all_labels() -> Dict[str, str]:
    """Get all custom genre labels as {key: label}."""
    genres = load_genres()
    return {g["key"]: g["label"] for g in genres if "key" in g and "label" in g}


def get_all_prompts() -> Dict[str, str]:
    """Get all custom genre prompts as {key: prompt}."""
    genres = load_genres()
    return {g["key"]: g["prompt"] for g in genres if "key" in g and "prompt" in g}


def get_all_meta() -> Dict[str, Dict[str, str]]:
    """Get all custom genre metadata as {key: meta}."""
    genres = load_genres()
    return {g["key"]: normalize_category_meta(g.get("meta")) for g in genres if "key" in g}
