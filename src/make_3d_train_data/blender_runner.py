import json
import os
from pathlib import Path
import subprocess
from .doctor import find_blender

class BlenderNotFoundError(RuntimeError): pass
class BlenderRenderError(RuntimeError): pass

def render_scene(scene, config, scene_path, result_path, image_path, blender_bin=None):
    binary=find_blender(blender_bin, config["blender"].get("binary"))
    if not binary: raise BlenderNotFoundError("Blender was not found. Install Blender or use --blender-bin / BLENDER_BIN / blender.binary, then run doctor.")
    assets={name:str(Path(path).resolve()) for name,path in config["assets"].items()}
    for path in assets.values():
        if not Path(path).is_file():
            raise BlenderRenderError(f"Master asset not found: {path}")
    payload={"scene":scene.to_dict(),"render":{"width":config["output"]["image_width"],"height":config["output"]["image_height"],"samples":config["blender"]["samples"],"engine":config["blender"]["engine"],"assets":assets,"image_path":str(Path(image_path).resolve()),"result_path":str(Path(result_path).resolve())}}
    Path(scene_path).write_text(json.dumps(payload),encoding="utf-8")
    entry=Path(__file__).parent/"blender"/"render_entry.py"
    env=os.environ.copy(); src=str(Path(__file__).parents[1]); env["PYTHONPATH"]=src+(os.pathsep+env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc=subprocess.run([binary,"--background","--factory-startup","--python",str(entry),"--",str(Path(scene_path).resolve())],capture_output=True,text=True,env=env)
    if proc.returncode or not Path(result_path).exists():
        tail="\n".join((proc.stdout+"\n"+proc.stderr).splitlines()[-30:])
        raise BlenderRenderError(f"Blender render failed (exit {proc.returncode}):\n{tail}")
    return json.loads(Path(result_path).read_text(encoding="utf-8"))
