import trimesh


def merge_meshes(meshes):

    print("Fusion des meshes...")

    combined = trimesh.util.concatenate(meshes)

    print("Mesh global créé")

    return combined