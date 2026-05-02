# -*- coding: utf-8 -*-
"""Trim white space from logo PNG, make white transparent, and save."""
from PIL import Image
from pathlib import Path
import numpy as np

src = Path(r"C:\tetie\ロゴ１.png")
dst = Path(r"C:\tetie\doorknock\assets\logo_trimmed.png")
dst.parent.mkdir(parents=True, exist_ok=True)

img = Image.open(src).convert("RGB")
arr = np.array(img)
print(f"Original: {img.size}")

# Detect non-white pixels (threshold < 250 in any channel)
mask = (arr[:, :, 0] < 250) | (arr[:, :, 1] < 250) | (arr[:, :, 2] < 250)
rows = np.any(mask, axis=1)
cols = np.any(mask, axis=0)

rmin, rmax = np.where(rows)[0][[0, -1]]
cmin, cmax = np.where(cols)[0][[0, -1]]
print(f"Content: rows {rmin}-{rmax}, cols {cmin}-{cmax}")

# Add small padding
pad = 20
rmin = max(0, rmin - pad)
rmax = min(arr.shape[0], rmax + pad)
cmin = max(0, cmin - pad)
cmax = min(arr.shape[1], cmax + pad)

cropped = img.crop((cmin, rmin, cmax, rmax))

# Make white/near-white pixels transparent
rgba = cropped.convert("RGBA")
data = np.array(rgba)
# Pixels where all RGB channels > 245 → transparent
white_mask = (data[:, :, 0] > 245) & (data[:, :, 1] > 245) & (data[:, :, 2] > 245)
data[white_mask, 3] = 0  # set alpha to 0
result = Image.fromarray(data, "RGBA")
result.save(dst, "PNG")
print(f"Cropped: {cropped.size}")
print(f"Transparent background applied")
print(f"Saved: {dst}")
