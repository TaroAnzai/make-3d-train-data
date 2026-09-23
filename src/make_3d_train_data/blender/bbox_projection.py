from bpy_extras.object_utils import world_to_camera_view

def project_bbox(scene,camera,obj,width,height):
    pts=[]
    for corner in obj.bound_box:
        co=world_to_camera_view(scene,camera,obj.matrix_world @ __import__('mathutils').Vector(corner))
        if co.z>0: pts.append((co.x*width,(1-co.y)*height))
    if not pts:return None
    x1=max(0,min(width,min(p[0] for p in pts))); y1=max(0,min(height,min(p[1] for p in pts))); x2=max(0,min(width,max(p[0] for p in pts))); y2=max(0,min(height,max(p[1] for p in pts)))
    return [x1,y1,x2,y2] if x2>x1 and y2>y1 else None

