from pathlib import Path

def yolo_line(canonical_id, bbox_xyxy, image_width, image_height):
    x1,y1,x2,y2 = bbox_xyxy
    return f"{canonical_id-1} {((x1+x2)/2)/image_width:.6f} {((y1+y2)/2)/image_height:.6f} {(x2-x1)/image_width:.6f} {(y2-y1)/image_height:.6f}"

def write_yolo(path, annotations, image_width, image_height):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(yolo_line(a["canonical_id"], a["bbox_xyxy"], image_width, image_height) for a in annotations) + ("\n" if annotations else ""), encoding="utf-8")

