"""Align the land cover labels to the NAIP grid and cut training tiles."""

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window

import config


def align_labels():
    """Resample the land cover onto the NAIP grid and return the canopy mask and land cover."""

    # The NAIP image defines the target grid.
    photo = rasterio.open(config.NAIP_FILE)

    # The transform maps each pixel in the study area to ground coordinates.
    target_transform = photo.window_transform(config.STUDY_AREA)

    # The NAIP profile is reused and modified for a single band of binary values.
    settings = photo.profile.copy()
    settings["count"] = 1            # Single band
    settings["dtype"] = "uint8"      # Binary values
    settings["nodata"] = 255         # Nodata value
    settings["width"] = config.STUDY_AREA.width
    settings["height"] = config.STUDY_AREA.height
    settings["transform"] = target_transform
    settings["compress"] = "lzw"     # Lossless compression

    photo_crs = photo.crs
    photo.close()

    # WarpedVRT reprojects on demand, so the 1.7 GB file is never fully loaded.
    answer_key = rasterio.open(config.LANDCOVER_FILE)

    virtual_reprojection = WarpedVRT(
        answer_key,
        crs=photo_crs,                     # NAIP coordinate system
        transform=target_transform,        # NAIP grid
        width=config.STUDY_AREA.width,
        height=config.STUDY_AREA.height,
        resampling=Resampling.mode,        # Majority class, as the values are categorical
    )

    landcover = virtual_reprojection.read(1)

    virtual_reprojection.close()
    answer_key.close()

    # The eight classes are reduced to a binary canopy mask.
    canopy_mask = (landcover == config.CANOPY_CLASS).astype("uint8")

    # The aligned mask is saved to avoid repeating this step.
    output = rasterio.open(config.ALIGNED_LABELS_FILE, "w", **settings)
    output.write(canopy_mask, 1)
    output.close()

    # The mean of a binary array equals the canopy fraction (the NYC average is 0.22).
    canopy_fraction = canopy_mask.mean()
    print("Fraction of the study area that is canopy:", round(canopy_fraction, 3))

    if canopy_fraction < 0.02 or canopy_fraction > 0.95:
        print("WARNING: that number looks wrong.")
        print("The two files probably aren't overlapping. Check your study area.")

    return canopy_mask, landcover

def cut_chips(landcover):
    """Divide the study area into 256 pixel tiles and save each as an .npz file."""

    photo = rasterio.open(config.NAIP_FILE)
    aligned = rasterio.open(config.ALIGNED_LABELS_FILE)
    canopy_mask = aligned.read(1)
    aligned.close()

    tile_size = config.CHIP_SIZE
    tiles_saved = 0
    tiles_skipped = 0

    # The study area is traversed in tile-sized steps.
    last_row = config.STUDY_AREA.height - tile_size + 1
    last_col = config.STUDY_AREA.width - tile_size + 1

    for row in range(0, last_row, tile_size):
        for col in range(0, last_col, tile_size):

            # Row and column are relative to the study area, so the offsets are added.
            read_window = Window(
                config.STUDY_AREA.col_off + col,
                config.STUDY_AREA.row_off + row,
                tile_size,
                tile_size,
            )
            image_tile = photo.read(window=read_window)

            # The labels are already cropped to the study area.
            mask_tile = canopy_mask[row:row + tile_size, col:col + tile_size]
            landcover_tile = landcover[row:row + tile_size, col:col + tile_size]

            # Tiles consisting mostly of nodata border are excluded from training.
            brightness = image_tile.sum(axis=0)
            fraction_black = (brightness == 0).mean()

            if fraction_black > 0.10:
                tiles_skipped = tiles_skipped + 1
                continue

            # Row and column are zero-padded so the files sort in order.
            filename = "chip_" + str(row).zfill(5) + "_" + str(col).zfill(5) + ".npz"
            filepath = config.CHIPS_FOLDER / filename

            np.savez_compressed(
                filepath,
                img=image_tile,
                msk=mask_tile,
                lc8=landcover_tile,
                row=row,
                col=col,
            )
            tiles_saved = tiles_saved + 1

    photo.close()
    print("Saved", tiles_saved, "tiles. Skipped", tiles_skipped, "(incomplete tile data).")

def load_chips():
    """Load all saved tiles into a list of dictionaries."""

    chips = []
    filepaths = sorted(config.CHIPS_FOLDER.glob("*.npz"))

    for filepath in filepaths:
        saved = np.load(filepath)

        chip = {
            "img": saved["img"],
            "msk": saved["msk"],
            "lc8": saved["lc8"],
            "row": int(saved["row"]),
            "col": int(saved["col"]),
        }
        chips.append(chip)

    return chips