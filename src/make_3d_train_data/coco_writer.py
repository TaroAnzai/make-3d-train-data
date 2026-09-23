import json
from pathlib import Path
from .class_defs import coco_categories

class CocoWriter:
    def __init__(self):
        self.images, self.annotations = [], []
    def add_image(self, image_id, file_name, width, height, annotations=()):
        self.images.append({"id": image_id, "file_name": file_name, "width": width, "height": height})
        for item in annotations:
            bbox = item["bbox_xywh"]
            self.annotations.append({"id": len(self.annotations)+1, "image_id": image_id, "category_id": item["canonical_id"], "bbox": bbox, "area": bbox[2]*bbox[3], "iscrowd": 0})
    def data(self): return {"info": {"description": "Synthetic mahjong tiles", "version": "1.0"}, "licenses": [], "images": self.images, "annotations": self.annotations, "categories": coco_categories()}
    def write(self, path):
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.data(), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

