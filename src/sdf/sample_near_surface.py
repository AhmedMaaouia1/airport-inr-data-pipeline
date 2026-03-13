import numpy as np


def sample_near_surface(surface_points, sigma=0.02):

    noise = np.random.normal(scale=sigma, size=surface_points.shape)

    near_surface = surface_points + noise

    return near_surface