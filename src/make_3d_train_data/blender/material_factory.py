from pathlib import Path
import bpy

def _solid(name, color, roughness=.32):
    mat=bpy.data.materials.new(name); mat.diffuse_color=(*color,1); mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF"); bsdf.inputs["Base Color"].default_value=(*color,1); bsdf.inputs["Roughness"].default_value=roughness
    return mat

def apply_material(obj, texture_path):
    body=_solid(obj.name+"_ivory_body",(.91,.89,.82),.4)
    back=_solid(obj.name+"_orange_back",(.82,.25,.025),.38)
    mat=_solid(obj.name+"_face",(.94,.93,.87),.38)
    bsdf=mat.node_tree.nodes.get("Principled BSDF")
    # The image is projected from above; Generated coordinates keep this self-contained.
    image=bpy.data.images.load(str(Path(texture_path)))
    tex=mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image=image; tex.projection="FLAT"
    coord=mat.node_tree.nodes.new("ShaderNodeTexCoord")
    mix=mat.node_tree.nodes.new("ShaderNodeMixRGB"); mix.blend_type="MIX"
    mix.inputs[1].default_value=(.94,.93,.87,1)
    mat.node_tree.links.new(coord.outputs["Generated"],tex.inputs["Vector"])
    mat.node_tree.links.new(tex.outputs["Alpha"],mix.inputs[0])
    mat.node_tree.links.new(tex.outputs["Color"],mix.inputs[2])
    mat.node_tree.links.new(mix.outputs["Color"],bsdf.inputs["Base Color"])
    obj.data.materials.append(body); obj.data.materials.append(mat); obj.data.materials.append(back)
    if not obj.get("layered_tile_materials"):
        for polygon in obj.data.polygons:
            polygon.material_index=1 if polygon.normal.z>.5 else (2 if polygon.normal.z<-.5 else 0)
