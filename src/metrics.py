"""Data splitting, NDVI calculation, and scoring."""

import numpy as np


def split_chips(chips):
    """Split the tiles 60/20/20 by column position to prevent spatial leakage."""

    # Unique column positions, ordered from left to right.
    all_columns = []
    for chip in chips:
        if chip["col"] not in all_columns:
            all_columns.append(chip["col"])
    all_columns.sort()

    # Split boundaries at 60% and 80% of the columns.
    train_end_index = int(0.60 * len(all_columns))
    val_end_index = int(0.80 * len(all_columns))

    train_boundary = all_columns[train_end_index]
    val_boundary = all_columns[val_end_index]

    train_chips = []
    val_chips = []
    test_chips = []

    for chip in chips:
        if chip["col"] < train_boundary:
            train_chips.append(chip)
        elif chip["col"] < val_boundary:
            val_chips.append(chip)
        else:
            test_chips.append(chip)

    print("Training tiles:  ", len(train_chips))
    print("Validation tiles:", len(val_chips))
    print("Test tiles:      ", len(test_chips))

    return train_chips, val_chips, test_chips


def calculate_ndvi(image):
    """Calculate NDVI as (NIR - red) / (NIR + red), with bands ordered R, G, B, NIR."""

    # Values are cast to float, as uint8 subtraction wraps around (50 - 100 = 206).
    red = image[0].astype("float32")
    near_infrared = image[3].astype("float32")

    difference = near_infrared - red
    total = near_infrared + red

    # A small constant prevents division by zero on nodata pixels.
    ndvi = difference / (total + 0.000001)

    return ndvi


def score_prediction(predicted, truth):
    """Calculate IoU, precision, recall, and F1 against the reference labels."""

    predicted = predicted.astype(bool)
    truth = truth.astype(bool)

    # True positives, false positives, and false negatives.
    true_positives = np.sum(predicted & truth)     # Correctly predicted canopy
    false_positives = np.sum(predicted & ~truth)   # Incorrectly predicted canopy
    false_negatives = np.sum(~predicted & truth)   # Missed canopy

    tiny = 0.000000001  # Prevents division by zero

    # Proportion of predicted canopy that is correct.
    precision = true_positives / (true_positives + false_positives + tiny)

    # Proportion of actual canopy that was detected.
    recall = true_positives / (true_positives + false_negatives + tiny)

    # Harmonic mean of precision and recall.
    f1 = 2 * precision * recall / (precision + recall + tiny)

    # Overlap divided by combined area.
    iou = true_positives / (true_positives + false_positives + false_negatives + tiny)

    results = {
        "iou": iou,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
    return results

def find_best_ndvi_threshold(chips):
    """Return the NDVI threshold with the highest F1 score on the training tiles."""

    # All tiles are flattened into single arrays of NDVI values and labels.
    all_ndvi_values = []
    all_truth_values = []

    for chip in chips:
        ndvi = calculate_ndvi(chip["img"])
        all_ndvi_values.append(ndvi.ravel())      # Flattened to one dimension
        all_truth_values.append(chip["msk"].ravel())

    ndvi_flat = np.concatenate(all_ndvi_values)
    truth_flat = np.concatenate(all_truth_values)

    best_threshold = None
    best_f1 = -1

    # The range begins below zero, as senescent November foliage has lower NDVI.
    for threshold in np.arange(-0.10, 0.60, 0.02):
        prediction = ndvi_flat > threshold
        scores = score_prediction(prediction, truth_flat)

        if scores["f1"] > best_f1:
            best_f1 = scores["f1"]
            best_threshold = threshold

    print("Best cutoff:", round(best_threshold, 2))
    print("F1 on training data:", round(best_f1, 3))

    return best_threshold