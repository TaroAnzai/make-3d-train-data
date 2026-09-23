import math
from mathutils import Vector
import bpy

def create_camera(desc):
    tilt=math.radians(desc["tilt_deg"]); yaw=math.radians(desc["yaw_deg"]); dist=desc["distance"]
    target=Vector((desc.get("target_x",0),desc.get("target_y",0),desc.get("target_z",0)))
    loc=(target.x+dist*math.sin(tilt)*math.sin(yaw),target.y-dist*math.sin(tilt)*math.cos(yaw),target.z+dist*math.cos(tilt))
    bpy.ops.object.camera_add(location=loc); cam=bpy.context.object
    direction=target-cam.location; cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler(); cam.rotation_euler.rotate_axis("Z",math.radians(desc["roll_deg"]))
    cam.data.lens=desc.get("lens_mm",52); cam.data.dof.use_dof=desc.get("dof_enabled",False); cam.data.dof.focus_distance=desc.get("focus_distance",dist); cam.data.dof.aperture_fstop=desc.get("aperture_fstop",5.6)
    bpy.context.scene.camera=cam; return cam
