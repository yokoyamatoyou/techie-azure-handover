from __future__ import annotations

import core.sitemap_analyzer as sitemap_mod


def test_fetch_sitemap_urls_aggregates_all_child_sitemaps(monkeypatch) -> None:
    root = "https://example.com"
    xml_map = {
        f"{root}/sitemap.xml": """
            <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <sitemap><loc>https://example.com/sitemap-pages.xml</loc></sitemap>
              <sitemap><loc>https://example.com/sitemap-blog.xml</loc></sitemap>
            </sitemapindex>
        """,
        f"{root}/sitemap-pages.xml": """
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <url><loc>https://example.com/</loc><lastmod>2026-04-01</lastmod></url>
              <url><loc>https://example.com/about</loc><lastmod>2026-04-02</lastmod></url>
            </urlset>
        """,
        f"{root}/sitemap-blog.xml": """
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <url><loc>https://example.com/blog/a</loc><lastmod>2026-04-03</lastmod></url>
              <url><loc>https://example.com/about</loc><lastmod>2026-04-04</lastmod></url>
            </urlset>
        """,
    }

    def fake_fetch(url: str):  # noqa: ANN001
        payload = xml_map.get(url)
        if payload is None:
            return None, 404
        return payload, 200

    monkeypatch.setattr(sitemap_mod, "_fetch_xml", fake_fetch)

    result = sitemap_mod.fetch_sitemap_urls(f"{root}/products")

    assert result["error"] is None
    assert result["total_urls"] == 3
    assert result["parsed_sitemaps"] == 3
    assert result["sampled_count"] == 3
    assert "https://example.com/blog/a" in result["sampled_urls"]
    about_entry = next(item for item in result["entries"] if item["url"] == "https://example.com/about")
    assert about_entry["lastmod"] == "2026-04-04"


def test_fetch_sitemap_urls_keeps_media_hints_from_child_sitemaps(monkeypatch) -> None:
    root = "https://example.com"
    xml_map = {
        f"{root}/sitemap.xml": """
            <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
              <sitemap><loc>https://example.com/sitemap-image.xml</loc></sitemap>
              <sitemap><loc>https://example.com/sitemap-video.xml</loc></sitemap>
            </sitemapindex>
        """,
        f"{root}/sitemap-image.xml": """
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                    xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
              <url>
                <loc>https://example.com/gallery</loc>
                <image:image><image:loc>https://example.com/a.jpg</image:loc></image:image>
              </url>
            </urlset>
        """,
        f"{root}/sitemap-video.xml": """
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
                    xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
              <url>
                <loc>https://example.com/movie</loc>
                <video:video><video:title>movie</video:title></video:video>
              </url>
            </urlset>
        """,
    }

    def fake_fetch(url: str):  # noqa: ANN001
        payload = xml_map.get(url)
        if payload is None:
            return None, 404
        return payload, 200

    monkeypatch.setattr(sitemap_mod, "_fetch_xml", fake_fetch)

    result = sitemap_mod.fetch_sitemap_urls(f"{root}/gallery")

    assert result["media_hints"]["image_sitemap_detected"] is True
    assert result["media_hints"]["video_sitemap_detected"] is True
    assert "https://example.com/sitemap-image.xml" in result["source_sitemaps"]
