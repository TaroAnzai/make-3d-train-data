import json,sys
from pathlib import Path

# Blender sanitizes or ignores an external PYTHONPATH in some distributions.
# Locate this source tree from the entry script so headless execution remains
# independent of Blender's bundled Python environment.
SOURCE_ROOT = Path(__file__).resolve().parents[2]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import bpy
from make_3d_train_data.blender.scene_builder import build_scene
from make_3d_train_data.blender.bbox_projection import project_bbox

def main():
    path=Path(sys.argv[sys.argv.index("--")+1]); payload=json.loads(path.read_text()); data,render=payload["scene"],payload["render"]
    objects,cam=build_scene(data,render["texture_dir"]); scene=bpy.context.scene
    available={item.identifier for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    requested=render["engine"]
    if requested not in available and requested=="BLENDER_EEVEE_NEXT" and "BLENDER_EEVEE" in available:
        requested="BLENDER_EEVEE"
    if requested not in available:
        raise ValueError(f"Render engine {render['engine']!r} is unavailable; available engines: {sorted(available)}")
    scene.render.engine=requested
    scene.render.resolution_x=render["width"]; scene.render.resolution_y=render["height"]; scene.render.resolution_percentage=100
    try: scene.view_settings.look="AgX - Medium High Contrast"
    except TypeError: pass
    scene.render.image_settings.file_format="JPEG"; scene.render.filepath=render["image_path"]
    if hasattr(scene,"eevee"): scene.eevee.taa_render_samples=render["samples"]
    bpy.ops.render.render(write_still=True)
    annotations=[]
    for obj,tile in objects:
        box=project_bbox(scene,cam,obj,render["width"],render["height"])
        if box:
            x1,y1,x2,y2=box; annotations.append({"canonical_id":tile["class_id"],"class":tile["class_name"],"bbox_xyxy":box,"bbox_xywh":[x1,y1,x2-x1,y2-y1],"position_3d":[tile["x"],tile["y"],tile["z"]],"rotation_deg":[tile["rotation_x"],tile["rotation_y"],tile["rotation_z"]],"scale":tile["scale"],"face_down":tile.get("face_down",False),"occluded":False})
    Path(render["result_path"]).write_text(json.dumps({"annotations":annotations}))
if __name__=="__main__": main()
