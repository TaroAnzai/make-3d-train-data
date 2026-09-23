import bpy

def create_lighting(desc):
    bpy.ops.object.light_add(type="AREA",location=(-.35,-.25,.8)); key=bpy.context.object; key.data.energy=8*desc["intensity"]; key.data.shape="DISK"; key.data.size=.65
    bpy.ops.object.light_add(type="AREA",location=(.35,.2,.55)); bpy.context.object.data.energy=3*desc["intensity"]; bpy.context.object.data.size=.45
