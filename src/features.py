"""Per-pixel features for the Random Forest classifier."""
import numpy as np
from scipy.ndimage import uniform_filter
from metrics import calculate_ndvi

# The order must match the stacking order in build_features.
FEATURE_NAMES = ["red", "green", "blue", "nir", "ndvi", "texture_small", "texture_large"]


def texture(band, size):
    """Calculate local variance, where higher values indicate rougher surfaces."""
    band = band.astype("float32")
    # Variance equals the mean of the squares minus the square of the mean.
    return np.clip(uniform_filter(band * band, size) - uniform_filter(band, size) ** 2, 0, None)


def build_features(image):
    """Build a feature table for one tile, with one row per pixel."""
    # Texture is measured on NIR, which shows vegetation structure most clearly.
    layers = [*image.astype("float32"), calculate_ndvi(image), texture(image[3], 3), texture(image[3], 9)]
    # Shape (7, pixels) is transposed to one row per pixel, as scikit-learn requires.
    return np.stack(layers).reshape(len(layers), -1).T


def build_table(chips):
    """Build the feature table and canopy labels for a set of tiles."""
    return (np.concatenate([build_features(c["img"]) for c in chips]),
            np.concatenate([c["msk"].ravel() for c in chips]))