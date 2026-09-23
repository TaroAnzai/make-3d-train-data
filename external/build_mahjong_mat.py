"""Build a flat, photo-inspired 690 mm mahjong mat.

Run: blender -b --factory-startup --python external/build_mahjong_mat.py
Master: assets/masters/table_assets.blend
Exports: output/table_assets/
"""

from pathlib import Path
import math

import bpy
import bmesh


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "table_assets"
TEXTURES = OUT / "textures"
MASTER = ROOT / "assets" / "masters" / "table_assets.blend"
SIZE = 0.690
HALF = SIZE / 2
INNER_HALF = 0.327  # 18 mm wide border on the straight sides


def material(name, image_path, base_color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*[v / 255 for v in base_color], 1)
    nodes = mat.node_tree.nodes
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Surface color texture"
    tex.image = bpy.data.images.load(str(image_path))
    tex.image.pack()
    mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def rounded_square(half, radius, z, segments=12):
    result = []
    for cx, cy, start in (
        (half-radius, half-radius, 0),
        (-half+radius, half-radius, 90),
        (-half+radius, -half+radius, 180),
        (half-radius, -half+radius, 270),
    ):
        for j in range(segments + 1):
            a = math.radians(start + 90*j/segments)
            result.append((cx + radius*math.cos(a), cy + radius*math.sin(a), z))
    return result


def mesh_object(name, verts, faces, mat):
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    uv = mesh.uv_layers.new(name="Mat UV")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (co.x/SIZE + 0.5, co.y/SIZE + 0.5)
    return obj


def layered_outline(name, layers, material):
    vertices = [v for layer in layers for v in layer]
    count = len(layers[0])
    faces = []
    for k in range(len(layers)-1):
        a, b = k*count, (k+1)*count
        for i in range(count):
            j = (i+1) % count
            faces.append((a+i, a+j, b+j, b+i))
    return mesh_object(name, vertices, faces, material)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    OUT.mkdir(parents=True, exist_ok=True)
    MASTER.parent.mkdir(parents=True, exist_ok=True)
    felt_path = TEXTURES / "felt_teal.png"
    rubber_path = TEXTURES / "rubber_teal.png"
    if not felt_path.exists() or not rubber_path.exists():
        raise FileNotFoundError("Run python3 generate_mahjong_mat_textures.py first")
    felt = material("teal_felt", felt_path, (13, 105, 105), 0.98)
    rubber = material("teal_rubber_border", rubber_path, (11, 139, 148), 0.79)

    # Underside and border are separate meshes so the surface stays strictly flat.
    bottom = rounded_square(HALF, 0.014, 0)
    side = rounded_square(HALF, 0.014, 0.0038)
    edge = rounded_square(HALF-0.0012, 0.013, 0.0050)
    shoulder = rounded_square(HALF-0.004, 0.011, 0.0066)
    lip = rounded_square(INNER_HALF, 0.006, 0.0066)
    inner_wall = rounded_square(INNER_HALF, 0.006, 0.0044)
    frame = layered_outline("rubber_edge", [bottom, side, edge, shoulder, lip, inner_wall], rubber)

    # A thin base fills the underside and supports the felt.
    base = mesh_object("rubber_base", bottom + rounded_square(HALF, 0.014, 0.0038),
                       [tuple(reversed(range(len(bottom)))),
                        tuple(range(len(bottom), 2*len(bottom)))], rubber)
    # The felt is one planar polygon. Its top is 4.4 mm above the underside.
    top = rounded_square(INNER_HALF, 0.006, 0.0044)
    under = rounded_square(INNER_HALF, 0.006, 0.0038)
    count = len(top)
    felt_faces = [tuple(range(count))]
    felt_faces += [(i, (i+1)%count, count+(i+1)%count, count+i) for i in range(count)]
    felt_obj = mesh_object("flat_felt_playing_surface", top + under, felt_faces, felt)

    # A single mesh makes it straightforward to place as background geometry.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in (base, frame, felt_obj):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = felt_obj
    bpy.ops.object.join()
    mat_table = felt_obj
    mat_table.name = "mat_table"
    mat_table.data.name = "mat_table_mesh"
    mat_table["units"] = "meters"
    mat_table["outer_size_mm"] = 690
    mat_table["surface_is_flat"] = True
    mat_table["straight_border_width_mm"] = 18
    background_assets = bpy.data.collections.new("background assets")
    bpy.context.scene.collection.children.link(background_assets)
    for collection in list(mat_table.users_collection):
        collection.objects.unlink(mat_table)
    background_assets.objects.link(mat_table)
    for collection in list(bpy.data.collections):
        if collection != background_assets and not collection.objects and not collection.children:
            bpy.data.collections.remove(collection)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.length_unit = "MILLIMETERS"
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.world.color = (0.4, 0.4, 0.4)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
    bpy.ops.export_scene.gltf(filepath=str(OUT / "mat_table.glb"),
                              export_format="GLB", export_apply=True,
                              export_yup=True)
    print("Created", OUT)


if __name__ == "__main__":
    main()
