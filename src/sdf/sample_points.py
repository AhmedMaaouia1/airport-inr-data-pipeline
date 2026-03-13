import numpy as np


def sample_points(bounds, n_points=10000):

    min_x, min_y, max_x, max_y = bounds

    # hauteur max arbitraire pour l'aéroport
    min_z = 0
    max_z = 80

    x = np.random.uniform(min_x, max_x, n_points)
    y = np.random.uniform(min_y, max_y, n_points)
    z = np.random.uniform(min_z, max_z, n_points)

    points = np.vstack((x, y, z)).T

    return points