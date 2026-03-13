import open3d as o3d
import trimesh


def show_mesh(mesh):

    vertices = mesh.vertices
    faces = mesh.faces

    mesh_o3d = o3d.geometry.TriangleMesh()
    mesh_o3d.vertices = o3d.utility.Vector3dVector(vertices)
    mesh_o3d.triangles = o3d.utility.Vector3iVector(faces)

    mesh_o3d.compute_vertex_normals()

    o3d.visualization.draw_geometries([mesh_o3d])