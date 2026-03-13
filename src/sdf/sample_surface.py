import trimesh


def sample_surface(mesh, n_points=5000):

    points, _ = trimesh.sample.sample_surface(mesh, n_points)

    return points