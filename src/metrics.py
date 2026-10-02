"""Data splitting, NDVI calculation, and scoring."""
import numpy as np


def split_chips(chips):
    """Split the tiles 60/20/20 by column position to prevent spatial leakage."""
    columns = sorted({chip["col"] for chip in chips})
    train_end, val_end = columns[int(0.6 * len(columns))], columns[int(0.8 * len(columns))]
    train = [c for c in chips if c["col"] < train_end]
    val = [c for c in chips if train_end <= c["col"] < val_end]
    test = [c for c in chips if c["col"] >= val_end]
    print(f"Tiles: {len(train)} train, {len(val)} validation, {len(test)} test")
    return train, val, test


def calculate_ndvi(image):
    """Calculate NDVI as (NIR - red) / (NIR + red), with bands ordered R, G, B, NIR."""
    # Values are cast to float, as uint8 subtraction wraps around (50 - 100 = 206).
    red, nir = image[0].astype("float32"), image[3].astype("float32")
    return (nir - red) / (nir + red + 1e-6)


def flat_ndvi(chips):
    """Calculate NDVI for every pixel in a set of tiles, as one flat array."""
    return np.concatenate([calculate_ndvi(chip["img"]).ravel() for chip in chips])


def score(predicted, truth):
    """Calculate IoU, precision, recall, and F1 against the reference labels."""
    predicted, truth = predicted.astype(bool), truth.astype(bool)
    correct = np.sum(predicted & truth)
    false_alarms = np.sum(predicted & ~truth)
    misses = np.sum(~predicted & truth)
    precision, recall = correct / (correct + false_alarms + 1e-9), correct / (correct + misses + 1e-9)
    return {"iou": correct / (correct + false_alarms + misses + 1e-9), "precision": precision,
            "recall": recall, "f1": 2 * precision * recall / (precision + recall + 1e-9)}


def best_threshold(values, truth, candidates):
    """Return the candidate threshold with the highest F1 score."""
    return max(candidates, key=lambda t: score(values > t, truth)["f1"])

