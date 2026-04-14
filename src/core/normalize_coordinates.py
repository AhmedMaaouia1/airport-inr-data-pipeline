import numpy as np


def normalize_points(points):
    """
    Legacy normalization with single unified scale.
    Deprecated: Use normalize_points_separate() for better Z-axis resolution.
    """
    mins = points.min(axis=0)
    maxs = points.max(axis=0)

    center = (mins + maxs) / 2
    scale = (maxs - mins).max() / 2

    normalized = (points - center) / scale

    return normalized, center, scale


def normalize_points_separate(points):
    """
    Normalize coordinates with separate XY and Z scales for better neural network training.
    
    This approach handles the typical airport geometry where horizontal extent >> vertical extent.
    By normalizing separately, Z-axis gets full [-1, 1] range instead of being compressed.
    
    Args:
        points: (N, 3) array of 3D coordinates
        
    Returns:
        normalized: (N, 3) array with coordinates in [-1, 1] range
        centers: dict with 'xy' (2,) and 'z' (scalar) center offsets
        scales: dict with 'xy' (scalar) and 'z' (scalar) scale factors
        
    Example (denormalization for inference):
        points_original = np.empty_like(points_normalized)
        points_original[:, :2] = (points_normalized[:, :2] * scales['xy']) + centers['xy']
        points_original[:, 2] = (points_normalized[:, 2] * scales['z']) + centers['z']
    """
    mins = points.min(axis=0)
    maxs = points.max(axis=0)
    
    # XY normalization: preserve horizontal aspect ratio
    center_xy = (mins[:2] + maxs[:2]) / 2
    scale_xy = (maxs[:2] - mins[:2]).max() / 2  # max preserves aspect ratio
    
    # Z normalization: use full Z range for better vertical resolution
    center_z = (mins[2] + maxs[2]) / 2
    scale_z = (maxs[2] - mins[2]) / 2
    
    # Apply normalization
    normalized = np.empty_like(points, dtype=np.float32)
    normalized[:, :2] = (points[:, :2] - center_xy) / scale_xy
    normalized[:, 2] = (points[:, 2] - center_z) / scale_z
    
    centers = {
        'xy': center_xy.astype(np.float32),
        'z': float(center_z)
    }
    scales = {
        'xy': float(scale_xy),
        'z': float(scale_z)
    }
    
    return normalized, centers, scales