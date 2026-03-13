import numpy as np


def sample_free_space(bounds, n_points=5000):

    min_x, min_y, max_x, max_y = bounds

    min_z = 0
    max_z = 80

    x = np.random.uniform(min_x, max_x, n_points)
    y = np.random.uniform(min_y, max_y, n_points)
    z = np.random.uniform(min_z, max_z, n_points)

    return np.vstack((x, y, z)).T