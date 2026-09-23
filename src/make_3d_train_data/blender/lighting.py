import bpy

def create_lighting(desc):
    bpy.ops.object.light_add(type="AREA",location=(-3,-4,7)); key=bpy.context.object; key.data.energy=900*desc["intensity"]; key.data.shape="DISK"; key.data.size=5
    bpy.ops.object.light_add(type="AREA",location=(4,2,5)); bpy.context.object.data.energy=350*desc["intensity"]; bpy.context.object.data.size=4

