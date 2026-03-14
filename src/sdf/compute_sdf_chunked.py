import numpy as np
import trimesh


def compute_sdf_chunked(mesh, points, chunk_size=5000):

    distances = []

    total = len(points)

    for i in range(0, total, chunk_size):

        chunk = points[i:i + chunk_size]

        print(f"Processing chunk {i} → {i+len(chunk)}")

        d = trimesh.proximity.signed_distance(mesh, chunk)

        distances.append(d)

    return np.concatenate(distances)