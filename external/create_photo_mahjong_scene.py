"""Recreate photo_sample/34344494_s.jpg using the existing mat and tile masters.
Run from this directory: blender -b --python create_photo_mahjong_scene.py
"""
from pathlib import Path
import math
import sys
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "output" / "mahjong_photo_34344494"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(HERE))
from tile_asset import set_tile_type

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in list(bpy.data.collections):
    if coll.name != 'Collection' and coll.users == 0:
        bpy.data.collections.remove(coll)

with bpy.data.libraries.load(str(ROOT/'assets/masters/table_assets.blend'), link=False) as (src, dst):
    dst.objects = ['mat_table']
mat = dst.objects[0]
bpy.context.collection.objects.link(mat)
mat.name = 'mat_table_from_master'
# Preserve the packed felt and rubber textures while matching the deeper photo color.
for material in mat.data.materials:
    if material and material.use_nodes:
        nodes = material.node_tree.nodes
        bsdf = nodes.get('Principled BSDF')
        if bsdf and bsdf.inputs['Base Color'].is_linked:
            link = bsdf.inputs['Base Color'].links[0]
            source = link.from_socket
            material.node_tree.links.remove(link)
            tint = nodes.new('ShaderNodeMixRGB')
            tint.blend_type = 'MULTIPLY'
            tint.inputs[0].default_value = 1.0
            tint.inputs[2].default_value = (.045,.24,.13,1)
            material.node_tree.links.new(source,tint.inputs[1])
            material.node_tree.links.new(tint.outputs[0],bsdf.inputs['Base Color'])

with bpy.data.libraries.load(str(ROOT/'assets/blender/tiles_master.blend'), link=False) as (src, dst):
    dst.objects = ['master_tile']
    dst.images = [name for name in src.images if name in [*(f'{i}{s}' for s in 'mps' for i in range(1,10)), 'ton','nan','sha','pei','haku','hatsu','chun','5mr','5pr','5sr']]
master = dst.objects[0]
# Keep the source object in the file, but out of the visible scene.
masters = bpy.data.collections.new('Source master models')
bpy.context.scene.collection.children.link(masters)
masters.objects.link(master)
master.hide_render = True
master.hide_set(True)

surface = .0044
tile_h = .0165
counts = {}
face_materials = {}
def clear_face_material(code):
    if code in face_materials:
        return face_materials[code]
    mat = bpy.data.materials.new('photo_face_' + code)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'Face UV'
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images[code]
    mix = nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MIX'
    mix.inputs[1].default_value = (.87,.85,.79,1)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = .34
    output = nodes.new('ShaderNodeOutputMaterial')
    links = mat.node_tree.links
    links.new(uv.outputs['UV'], tex.inputs['Vector'])
    links.new(tex.outputs['Alpha'], mix.inputs[0])
    links.new(tex.outputs['Color'], mix.inputs[2])
    links.new(mix.outputs['Color'], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    face_materials[code] = mat
    return mat

def tile(code, name, xyz, rx=0, rz=0):
    ob = master.copy()
    ob.name = name
    ob.location = xyz
    ob.rotation_euler = (math.radians(rx), 0, math.radians(rz))
    bpy.context.collection.objects.link(ob)
    ob.hide_render = False
    ob.hide_set(False)
    # A missing face never shows on the orange-backed wall.
    set_tile_type(ob, code)
    ob.material_slots[2].material = clear_face_material(code)
    counts[name.split('_')[0]] = counts.get(name.split('_')[0],0)+1
    return ob

# The photographed player's thirteen upright tiles, from image left to right.
hand = ['2s','3s','4s','5sr','6s','7s','8s','7p','5pr','6p','8p','hatsu','hatsu']
for i, code in enumerate(hand):
    x = (i-6)*.02055
    tile(code, f'hand_{i+1:02d}_{code}', (x, -.230, surface+.014), rx=90)

# Foreground wall: seven orange backs across, two tiles high.
for level in range(2):
    for i in range(7):
        x = -.020 + (i-3)*.0198
        y = -.200 + (0.002 if level else 0)
        tile('haku', f'wall_front_{level+1}_{i+1:02d}',
             (x,y,surface+tile_h*(level+1)), rx=180)
# One face-up tile sits over the short foreground wall in the source image.
tile('1s','wall_front_dora_indicator',(-.0398,-.200,surface+tile_h*2),rx=0)

# Back edge of the wall, and the short right edge visible in the photograph.
for level in range(2):
    for i in range(11):
        tile('haku',f'wall_back_{level+1}_{i+1:02d}',
             ((i-5)*.0198,.030,surface+tile_h*(level+1)),rx=180)
    for i in range(5):
        tile('haku',f'wall_right_{level+1}_{i+1:02d}',
             (.180,-.025-i*.0278,surface+tile_h*(level+1)),rx=180,rz=90)
tile('haku','wall_right_stray',(.195,-.160,surface+tile_h),rx=180,rz=8)

# Discarded tiles behind the omitted central roulette. Their groups and
# near-regular spacing follow the photograph, without adding a roulette mesh.
rear = [
    ('2p',-.061,.225),('ton',-.037,.225),('chun',-.013,.225),
    ('4s',.011,.225),('1p',.035,.225),('haku',.059,.225),
    ('6m',-.061,.195),('5m',-.037,.195),('hatsu',-.013,.195),
    ('2s',.011,.195),('9p',.035,.195),('3p',.059,.195),
]
for i,(code,_,_) in enumerate(rear):
    x = -.0508 + (i % 6)*.0198
    y = .005 - (i // 6)*.0278
    tile(code,f'discard_rear_{i+1:02d}',(x,y,surface),rz=180)

right_codes = [
    ['3s','5m','4p'], ['6s','7m','2p'], ['8s','1m','9p'],
    ['hatsu','3m','8p'], ['ton','5s','6p']
]
for row,codes in enumerate(right_codes):
    for col,code in enumerate(codes):
        tile(code,f'discard_right_{row+1:02d}_{col+1:02d}',
             (.076+col*.0278,.030-row*.0198,surface),rz=90)

front_codes = [
    ['7m','9m','sha','chun','chun','1p'],
    ['pei','6m','hatsu','2m','2m','pei'],
    ['1p','7m','hatsu','3p',None,None],
]
for row,codes in enumerate(front_codes):
    for col,code in enumerate(codes):
        if code:
            tile(code,f'discard_front_{row+1:02d}_{col+1:02d}',
                 (-.061+col*.0198,-.110-row*.0278,surface),rz=180)

# Neutral tabletop only frames the actual mat.
bgmat = bpy.data.materials.new('dark_tabletop')
bgmat.diffuse_color = (.095,.108,.105,1)
bgmat.use_nodes = True
bgmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.095,.108,.105,1)
bpy.ops.mesh.primitive_plane_add(size=3, location=(0,0,-.003))
bg=bpy.context.object
bg.name='studio_tabletop'
bg.data.materials.append(bgmat)

camera_data=bpy.data.cameras.new('Photo-matched perspective')
camera=bpy.data.objects.new('Photo-matched perspective',camera_data)
bpy.context.collection.objects.link(camera)
camera.location=(0,-.60,.29)
target=Vector((0,-.185,.005))
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
camera_data.type='PERSP'
camera_data.lens=58
bpy.context.scene.camera=camera

light_data=bpy.data.lights.new('large_softbox','AREA')
light=bpy.data.objects.new('large_softbox',light_data)
bpy.context.collection.objects.link(light)
light.location=(-.24,-.10,.85)
light_data.energy=80
light_data.shape='RECTANGLE'
light_data.size=1.1
light_data.size_y=.7

scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=16
scene.render.resolution_x=1280
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.filepath=str(OUT/'preview.png')
scene.world.color=(.38,.38,.38)
scene.view_settings.view_transform='AgX'
scene.camera.data.dof.use_dof=False
scene.render.film_transparent=False
scene.render.image_settings.color_mode='RGBA'
scene['reference_photo']='external/photo_sample/34344494_s.jpg'
scene['layout_note']='Hand, stacked walls, and three discard clusters; central roulette omitted.'
scene['tile_count']=sum(counts.values())
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'mahjong_photo_34344494.blend'))
bpy.ops.render.render(write_still=True)
print('Output:',OUT,'Tiles:',sum(counts.values()))
