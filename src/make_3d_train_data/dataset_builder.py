import json, random, shutil, tempfile
from pathlib import Path
import yaml
from PIL import Image, ImageEnhance, ImageFilter
from .blender_runner import render_scene
from .class_defs import CLASSES
from .coco_writer import CocoWriter
from .manifest_writer import ManifestWriter
from .scene_generator import generate_scenes
from .yolo_writer import write_yolo

def _postprocess(path, noise, seed):
    rng=random.Random(seed); im=Image.open(path).convert("RGB")
    im=ImageEnhance.Brightness(im).enhance(rng.uniform(*noise["brightness_range"]))
    im=ImageEnhance.Contrast(im).enhance(rng.uniform(*noise["contrast_range"]))
    if rng.random()<noise["blur_prob"]: im=im.filter(ImageFilter.GaussianBlur(rng.uniform(*noise["blur_sigma_range"])))
    im.save(path,"JPEG",quality=rng.randint(*map(int,noise["jpeg_quality_range"])))

def build_dataset(config, blender_bin=None):
    root=Path(config["output"]["root"])/config["output"]["dataset_name"]
    images=root/"images"; labels=root/"labels"; meta=root/"meta"
    for p in (images,labels,meta): p.mkdir(parents=True,exist_ok=True)
    coco=CocoWriter(); manifest=ManifestWriter(meta/"manifest.jsonl")
    (meta/"manifest.jsonl").write_text("",encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="mahjong_render_") as tmp:
        for i,scene in enumerate(generate_scenes(config),1):
            name=f"{i:06d}.jpg"; result=render_scene(scene,config,Path(tmp)/f"scene_{i}.json",Path(tmp)/f"result_{i}.json",images/name,blender_bin)
            _postprocess(images/name,scene.noise,scene.seed)
            anns=result["annotations"]
            if "coco" in config["output"]["formats"]: coco.add_image(i,name,config["output"]["image_width"],config["output"]["image_height"],anns)
            if "yolo" in config["output"]["formats"]: write_yolo(labels/"yolo"/f"{i:06d}.txt",anns,config["output"]["image_width"],config["output"]["image_height"])
            manifest.append({"image":name,"seed":scene.seed,"width":config["output"]["image_width"],"height":config["output"]["image_height"],"mode":scene.mode,"tiles":anns,"camera":scene.to_dict()["camera"],"lighting":scene.to_dict()["lighting"],"background":scene.background,"appearance":scene.appearance,"occlusion":scene.occlusion})
    if "coco" in config["output"]["formats"]: coco.write(labels/"instances.json")
    (meta/"classes.json").write_text(json.dumps([{"canonical_id":c.canonical_id,"name":c.name,"yolo_id":c.canonical_id-1} for c in CLASSES],indent=2)+"\n",encoding="utf-8")
    clean={k:v for k,v in config.items() if not k.startswith("_")}; (meta/"used_config.yaml").write_text(yaml.safe_dump(clean,sort_keys=False),encoding="utf-8")
    (meta/"generation_summary.json").write_text(json.dumps({"images":config["output"]["count"],"dataset":config["output"]["dataset_name"],"formats":config["output"]["formats"]},indent=2)+"\n",encoding="utf-8")
    return root
