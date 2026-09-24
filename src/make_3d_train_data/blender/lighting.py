import math

import bpy


def _temperature_rgb(kelvin):
    # Approximate black-body white balance, limited by config validation to indoor light.
    t = kelvin / 100
    red = 255 if t <= 66 else 329.698727446 * (t - 60) ** -.1332047592
    green = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -.0755148492
    blue = 0 if t <= 19 else (138.5177312231 * math.log(t - 10) - 305.0447927307 if t <= 66 else 255)
    return tuple(max(0, min(255, channel)) / 255 for channel in (red, green, blue))

def create_lighting(desc):
    color = _temperature_rgb(desc.get("color_temperature", 5000))
    bpy.ops.object.light_add(type="AREA", location=desc.get("key_position", (-.35, -.25, .8)))
    key = bpy.context.object
    key.data.energy = 8 * desc["intensity"]
    key.data.shape = "DISK"
    key.data.size = .65
    key.data.color = color
    bpy.ops.object.light_add(type="AREA", location=desc.get("fill_position", (.35, .2, .55)))
    fill = bpy.context.object
    fill.data.energy = 3 * desc["intensity"]
    fill.data.size = .45
    fill.data.color = color
