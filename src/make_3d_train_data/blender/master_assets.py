"""Load the reusable Blender masters and place tile instances on the mat."""

import math
from pathlib import Path

import bpy
from mathutils import Euler, Vector


TILE_CODES = {
    **{f"{number}{suit}": f"{number}{suit}" for suit in "mps" for number in range(1, 10)},
    "east": "ton", "south": "nan", "west": "sha", "north": "pei",
    "white": "haku", "green": "hatsu", "red": "chun",
    "red5m": "5mr", "red5p": "5pr", "red5s": "5sr",
}


def load_masters(tile_blend, mat_blend):
    for path in (tile_blend, mat_blend):
        if not Path(path).is_file():
            raise FileNotFoundError(f"Master asset is missing: {path}")
    with bpy.data.libraries.load(str(tile_blend), link=False) as (source, target):
        if "master_tile" not in source.objects:
            raise ValueError(f"master_tile is missing from {tile_blend}")
        target.objects = ["master_tile"]
        target.images = [code for code in TILE_CODES.values() if code in source.images]
    tile_master = target.objects[0]
    missing = set(TILE_CODES.values()) - set(bpy.data.images.keys())
    if missing:
        raise ValueError(f"Tile master is missing images: {sorted(missing)}")

    with bpy.data.libraries.load(str(mat_blend), link=False) as (source, target):
        if "mat_table" not in source.objects:
            raise ValueError(f"mat_table is missing from {mat_blend}")
        target.objects = ["mat_table"]
    mat = target.objects[0]
    bpy.context.collection.objects.link(mat)
    felt_slots = {i for i, material in enumerate(mat.data.materials) if material and "felt" in material.name.lower()}
    if not felt_slots:
        raise ValueError("The mat master has no felt material")
    surface_z = max(mat.data.vertices[index].co.z for polygon in mat.data.polygons
                    if polygon.material_index in felt_slots for index in polygon.vertices)
    return tile_master, surface_z


def _face_material(code):
    name = f"tile_face_{code}"
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials["tile_face"].copy()
        material.name = name
        uv = material.node_tree.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "Face UV"
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.image = bpy.data.images[code]
                if node.name == "Image Texture":
                    material.node_tree.links.new(uv.outputs["UV"], node.inputs["Vector"])
    return material


def create_tile(master, tile, surface_z):
    code = TILE_CODES[tile["class_name"]]
    obj = master.copy()
    obj.name = f"tile_{tile['class_id']}_{tile['class_name']}"
    obj.rotation_euler = Euler(tuple(math.radians(tile[key]) for key in
                                    ("rotation_x", "rotation_y", "rotation_z")), "XYZ")
    obj.scale = (tile["scale"],) * 3
    rotated = obj.rotation_euler.to_matrix()
    lowest = min((rotated @ Vector(corner)).z * tile["scale"] for corner in obj.bound_box)
    obj.location = (tile["x"], tile["y"], surface_z + tile["z"] - lowest)
    bpy.context.collection.objects.link(obj)
    obj.material_slots[2].link = "OBJECT"
    obj.material_slots[2].material = _face_material(code)
    obj["tile_code"] = code
    return obj
