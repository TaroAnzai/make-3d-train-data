from dataclasses import dataclass

@dataclass(frozen=True)
class BBox:
    x1: float; y1: float; x2: float; y2: float
    @property
    def width(self): return self.x2 - self.x1
    @property
    def height(self): return self.y2 - self.y1
    def xyxy(self): return [self.x1, self.y1, self.x2, self.y2]
    def xywh(self): return [self.x1, self.y1, self.width, self.height]

def clip_bbox(box: BBox | list[float], width: int, height: int) -> BBox | None:
    if not isinstance(box, BBox): box = BBox(*map(float, box))
    clipped = BBox(max(0., min(float(width), box.x1)), max(0., min(float(height), box.y1)), max(0., min(float(width), box.x2)), max(0., min(float(height), box.y2)))
    return clipped if clipped.width > 0 and clipped.height > 0 else None

def bbox_from_points(points, width: int, height: int):
    points = list(points)
    if not points: return None
    return clip_bbox(BBox(min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)), width, height)

