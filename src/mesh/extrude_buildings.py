import trimesh


def extrude_buildings(gdf, default_height=15):

    meshes = []

    for _, row in gdf.iterrows():

        polygon = row.geometry

        height = row.height

        if height is None:
            height = default_height

        mesh = trimesh.creation.extrude_polygon(
            polygon,
            height
        )

        meshes.append(mesh)

    return meshes