"""Per-pixel features for the Random Forest classifier."""

import numpy as np
from scipy.ndimage import uniform_filter

from metrics import calculate_ndvi


# The order must match the stacking order below.
FEATURE_NAMES = [
    "red",
    "green",
    "blue",
    "infrared",
    "ndvi",
    "texture_small",
    "texture_large",
]


def measure_texture(band, window_size):
    """Calculate local variance, where higher values indicate rougher surfaces."""

    values = band.astype("float32")

    # Local mean within the window.
    local_average = uniform_filter(values, window_size)
    local_average_of_squares = uniform_filter(values * values, window_size)

    variance = local_average_of_squares - (local_average * local_average)

    # Rounding error can produce small negative values.
    variance = np.clip(variance, 0, None)

    return variance


def build_features_for_chip(image):
    """Build a feature table for one tile, with one row per pixel."""

    red = image[0].astype("float32")
    green = image[1].astype("float32")
    blue = image[2].astype("float32")
    infrared = image[3].astype("float32")

    ndvi = calculate_ndvi(image)

    # Texture is measured on NIR, which shows vegetation structure most clearly.
    texture_small = measure_texture(infrared, 3)
    texture_large = measure_texture(infrared, 9)

    # Same order as FEATURE_NAMES.
    feature_list = [
        red,
        green,
        blue,
        infrared,
        ndvi,
        texture_small,
        texture_large,
    ]

    # Shape (7, height, width).
    stacked = np.stack(feature_list, axis=0)

    # Each feature is flattened to a single row.
    number_of_features = stacked.shape[0]
    number_of_pixels = stacked.shape[1] * stacked.shape[2]
    flattened = stacked.reshape(number_of_features, number_of_pixels)

    # Transposed to one row per pixel, as scikit-learn requires.
    return flattened.T


def build_features_for_chips(chips):
    """Build the feature table and canopy labels for a set of tiles."""

    feature_blocks = []
    answer_blocks = []

    for chip in chips:
        features = build_features_for_chip(chip["img"])
        answers = chip["msk"].ravel()

        feature_blocks.append(features)
        answer_blocks.append(answers)

    all_features = np.concatenate(feature_blocks)
    all_answers = np.concatenate(answer_blocks)

    return all_features, all_answers