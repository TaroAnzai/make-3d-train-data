"""Switch the face of an object copied from tiles_master.blend.

In Blender: from tile_asset import set_tile_type
            tile = bpy.data.objects['master_tile'].copy()
            bpy.context.collection.objects.link(tile)
            set_tile_type(tile, '5sr')
"""

import bpy


TILE_CODES = (
    *(f"{n}{suit}" for suit in "mps" for n in range(1, 10)),
    "ton", "nan", "sha", "pei", "haku", "hatsu", "chun",
    "5mr", "5pr", "5sr",
)


def set_tile_type(obj, code):
    """Give one tile copy its own face material while sharing the master mesh."""
    if code not in TILE_CODES:
        raise ValueError(f"Unknown tile code: {code}")
    if obj.type != "MESH" or len(obj.material_slots) < 3:
        raise TypeError("Expected a copy of the master_tile mesh")
    image = bpy.data.images.get(code)
    if image is None:
        raise KeyError(f"Tile image {code!r} is missing from the blend file")
    material = bpy.data.materials.get(f"tile_face_{code}")
    if material is None:
        material = bpy.data.materials["tile_face"].copy()
        material.name = f"tile_face_{code}"
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE":
                node.image = image
    slot = obj.material_slots[2]
    slot.link = "OBJECT"
    slot.material = material
    obj["tile_code"] = code
    return obj
