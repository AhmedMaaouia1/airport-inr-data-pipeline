import trimesh


def compute_sdf(mesh, points):

    print("Calcul des distances...")

    distances = trimesh.proximity.signed_distance(mesh, points)

    return distances