import bpy
from .camera import create_camera
from .lighting import create_lighting
from .master_assets import create_tile, load_masters

def build_scene(data, assets):
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_plane_add(size=1.6, location=(0, 0, -.003))
    tabletop = bpy.context.object
    tabletop.name = "dark_tabletop"
    material = bpy.data.materials.new("dark_tabletop")
    material.use_nodes = True
    material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.06, .065, .06, 1)
    material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = .85
    tabletop.data.materials.append(material)
    tile_master, surface_z = load_masters(assets["tile_blend"], assets["mat_blend"])
    objects=[]
    for tile in data["tiles"]:
        obj=create_tile(tile_master,tile,surface_z); objects.append((obj,tile))
    cam=create_camera(data["camera"]); create_lighting(data["lighting"])
    world=bpy.context.scene.world; world.color=(.32,.32,.32)
    return objects,cam
