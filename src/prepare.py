"""Align the land cover labels to the NAIP grid and cut training tiles."""
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window
import config


def align_labels():
    """Resample the land cover onto the NAIP grid and return the canopy mask and land cover."""
    area = config.STUDY_AREA
    with rasterio.open(config.NAIP_FILE) as photo:
        transform, crs = photo.window_transform(area), photo.crs
        # The NAIP profile is reused and modified for a single band of binary values.
        profile = dict(photo.profile, count=1, dtype="uint8", nodata=255, compress="lzw",
                       transform=transform, width=area.width, height=area.height)
    # WarpedVRT reprojects on demand; majority resampling is used because the classes are categorical.
    with rasterio.open(config.LANDCOVER_FILE) as source, WarpedVRT(
            source, crs=crs, transform=transform, width=area.width, height=area.height,
            resampling=Resampling.mode) as vrt:
        landcover = vrt.read(1)
    canopy_mask = (landcover == config.CANOPY_CLASS).astype("uint8")
    with rasterio.open(config.LABELS_FILE, "w", **profile) as output:
        output.write(canopy_mask, 1)
    # The mean of a binary array equals the canopy fraction (the NYC average is 0.22).
    print("Canopy fraction:", round(canopy_mask.mean(), 3))
    return canopy_mask, landcover


def cut_chips(landcover):
    """Divide the study area into 256 pixel tiles and save each as an .npz file."""
    size, area = config.CHIP_SIZE, config.STUDY_AREA
    canopy_mask = (landcover == config.CANOPY_CLASS).astype("uint8")
    saved = 0
    with rasterio.open(config.NAIP_FILE) as photo:
        for row in range(0, area.height - size + 1, size):
            for col in range(0, area.width - size + 1, size):
                # Row and column are relative to the study area, so the offsets are added.
                image = photo.read(window=Window(area.col_off + col, area.row_off + row, size, size))
                # Tiles containing any nodata pixels are excluded.
                if (image.sum(axis=0) == 0).any():
                    continue
                # The same window is cut from both label arrays.
                cells = np.s_[row:row + size, col:col + size]
                np.savez_compressed(config.CHIPS_FOLDER / f"chip_{row:05d}_{col:05d}.npz", img=image,
                                    msk=canopy_mask[cells], lc8=landcover[cells], row=row, col=col)
                saved += 1
    print("Tiles saved:", saved)


def load_chips():
    """Load all saved tiles into a list of dictionaries."""
    chips = []
    for path in sorted(config.CHIPS_FOLDER.glob("*.npz")):
        data = np.load(path)
        chips.append({"img": data["img"], "msk": data["msk"], "lc8": data["lc8"],
                      "row": int(data["row"]), "col": int(data["col"])})
    return chips


def flatten(chips, key):
    """Join one array from every tile into a single flat array."""
    return np.concatenate([chip[key].ravel() for chip in chips])