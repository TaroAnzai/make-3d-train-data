import bpy
from .camera import create_camera
from .lighting import create_lighting
from .material_factory import apply_material
from .tile_factory import create_tile

def build_scene(data, texture_dir):
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_plane_add(size=60,location=(0,0,-.02)); floor=bpy.context.object
    color=data.get("background",{}).get("color",[.07,.22,.12]); mat=bpy.data.materials.new("table"); mat.diffuse_color=(*color,1); mat.use_nodes=True
    nodes=mat.node_tree.nodes; links=mat.node_tree.links; bsdf=nodes["Principled BSDF"]; bsdf.inputs["Base Color"].default_value=(*color,1); bsdf.inputs["Roughness"].default_value=.82
    noise=nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value=42; noise.inputs["Detail"].default_value=3; noise.inputs["Roughness"].default_value=.75
    bump=nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value=.16; bump.inputs["Distance"].default_value=.055
    links.new(noise.outputs["Fac"],bump.inputs["Height"]); links.new(bump.outputs["Normal"],bsdf.inputs["Normal"]); floor.data.materials.append(mat)
    objects=[]
    for tile in data["tiles"]:
        obj=create_tile(tile); apply_material(obj,f"{texture_dir}/{tile['class_name']}.png"); objects.append((obj,tile))
    cam=create_camera(data["camera"]); create_lighting(data["lighting"])
    world=bpy.context.scene.world; world.color=tuple(component*.22 for component in color)
    return objects,cam
