import numpy as np


def normalize_points(points):

    mins = points.min(axis=0)
    maxs = points.max(axis=0)

    center = (mins + maxs) / 2
    scale = (maxs - mins).max() / 2

    normalized = (points - center) / scale

    return normalized, center, scale