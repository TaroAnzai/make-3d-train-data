"""Build the reusable 37-face mahjong tile asset with Blender background mode.

Run: blender -b --python external/build_tiles_master.py -- --project-root .
"""

import argparse
from pathlib import Path
import shutil
import sys

import bpy


SOURCE_NAMES = {
    **{f"{n}m": f"Man{n}.png" for n in range(1, 10)},
    **{f"{n}p": f"Pin{n}.png" for n in range(1, 10)},
    **{f"{n}s": f"Sou{n}.png" for n in range(1, 10)},
    "ton": "Ton.png", "nan": "Nan.png", "sha": "Shaa.png", "pei": "Pei.png",
    "haku": "Haku.png", "hatsu": "Hatsu.png", "chun": "Chun.png",
    "5mr": "Man5-Dora.png", "5pr": "Pin5-Dora.png", "5sr": "Sou5-Dora.png",
}


def make_neutral_face(old_face, body):
    """Keep the source tile's crowned surface, without its Man1-specific grooves."""
    width = old_face.dimensions.x
    height = old_face.dimensions.y
    top_z = max(v.co.z for v in body.data.vertices)
    columns, rows = 65, 97
    vertices = []
    for row in range(rows):
        y = height * (row / (rows - 1) - 0.5)
        for column in range(columns):
            x = width * (column / (columns - 1) - 0.5)
            edge = min(width / 2 - abs(x), height / 2 - abs(y))
            t = min(1.0, max(0.0, edge / 0.00055))
            t = t * t * (3 - 2 * t)
            vertices.append((x, y, top_z + 0.000045 * (0.02 + 0.98 * t)))
    faces = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            i = row * columns + column
            faces.append((i, i + 1, i + columns + 1, i + columns))
    mesh = bpy.data.meshes.new("master_tile_mesh_face")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    uv = mesh.uv_layers.new(name="Face UV")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop_index in polygon.loop_indices:
            co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (co.x / 0.020 + 0.5, co.y / 0.028 + 0.5)
    face = bpy.data.objects.new("neutral_tile_face", mesh)
    bpy.context.collection.objects.link(face)
    face.data.materials.append(old_face.data.materials[0])
    return face


def use_artwork_colors(material):
    """The source Man1 shader recolors ink red/black; retain all PNG colors."""
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    artwork = nodes["Image Texture"]
    bsdf = nodes["Principled BSDF"]
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "Tile artwork over ivory"
    mix.blend_type = "MIX"
    mix.inputs[1].default_value = (0.896269, 0.879622, 0.83077, 1.0)
    links.new(artwork.outputs["Alpha"], mix.inputs[0])
    links.new(artwork.outputs["Color"], mix.inputs[2])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    root = args.project_root.resolve()
    source = root / "assets/masters/final_master_tile.blend"
    if not source.exists():
        source = root / "assets/masters/master_tile.blend"
    if not source.exists():
        raise FileNotFoundError("No existing master tile blend found")
    artwork = root / "external/riichi-mahjong-tiles/Export/Regular"
    texture_dir = root / "assets/textures/tiles"
    blend_path = root / "assets/blender/tiles_master.blend"
    texture_dir.mkdir(parents=True, exist_ok=True)
    blend_path.parent.mkdir(parents=True, exist_ok=True)
    for code, filename in SOURCE_NAMES.items():
        shutil.copyfile(artwork / filename, texture_dir / f"{code}.png")

    bpy.ops.wm.open_mainfile(filepath=str(source))
    body = bpy.data.objects["MASTER_TILE_ivory"]
    orange = bpy.data.objects["MASTER_TILE_orange"]
    old_face = bpy.data.objects["MASTER_TILE_face_relief"]
    body.data.materials[0].name = "tile_body_white"
    orange.data.materials[0].name = "tile_back_orange"
    face_material = old_face.data.materials[0]
    face_material.name = "tile_face"
    use_artwork_colors(face_material)
    face = make_neutral_face(old_face, body)
    for obj in list(bpy.data.objects):
        if obj not in (body, orange, face):
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in (body, orange):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for modifier in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in (body, orange, face):
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = "master_tile"
    body.data.name = "master_tile_mesh"
    assert [m.name for m in body.data.materials] == [
        "tile_body_white", "tile_back_orange", "tile_face"
    ]
    assert not body.modifiers, "Source modifiers need explicit review before joining"
    body["tile_code"] = "1m"
    body["tile_codes"] = ",".join(SOURCE_NAMES)
    body["face_material_slot"] = 2
    body["tile_face_uv"] = "Face UV"
    body["source_blend"] = source.name
    for image in list(bpy.data.images):
        if image.users == 0:
            bpy.data.images.remove(image)
    for code in SOURCE_NAMES:
        image = bpy.data.images.load(str(texture_dir / f"{code}.png"), check_existing=False)
        image.name = code
        image.pack()
        image.filepath = f"//../textures/tiles/{code}.png"
        image.use_fake_user = True
    for node in face_material.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            node.image = bpy.data.images["1m"]
    for material in list(bpy.data.materials):
        if material.users == 0:
            bpy.data.materials.remove(material)
    bpy.context.scene.camera = None
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print(f"CREATED {blend_path}; {len(SOURCE_NAMES)} textures; {len(body.data.polygons)} faces")


if __name__ == "__main__":
    main()
