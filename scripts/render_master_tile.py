"""Render a high-quality reference mahjong tile in Blender 4.x or newer."""

import argparse
import math
import sys
from array import array
from pathlib import Path

import bpy
from mathutils import Vector


MM = 0.001
TILE_HEIGHT_MM = 28.0
TILE_WIDTH_MM = 20.0
TILE_DEPTH_MM = 16.5
VISIBLE_ORANGE_HEIGHT_MM = 2.6
BODY_BEVEL_RADIUS_MM = 1.00
BASE_BEVEL_RADIUS_MM = 0.90
BEVEL_SEGMENTS = 8
TAPER_RATIO = 0.006
BOUNDARY_STEP_ENABLED = True
BOUNDARY_STEP_WIDTH_MM = 3.0
BOUNDARY_STEP_DEPTH_MM = 0.7
BOUNDARY_STEP_OFFSET_MM = 0.5
BOUNDARY_STEP_SHOULDER_MM = 0.45

BODY_BASE_COLOR = "F3F1EB"
BODY_ROUGHNESS = 0.18
BODY_SPECULAR = 0.46
BODY_IOR = 1.47
BODY_CLEARCOAT = 0.12
ORANGE_BASE_COLOR = "C98A2E"
ORANGE_ROUGHNESS = 0.23
ORANGE_SPECULAR = 0.42
ORANGE_IOR = 1.47
INK_BLACK = "1F2023"
INK_RED = "712D2B"
BACKGROUND_COLOR = "F5F5F2"
RENDER_SAMPLES = 512
RENDER_SIZE = 1024
KEY_POWER = 1.35
FILL_POWER = 0.12
RIM_POWER = 0.38
EXPOSURE = -0.85
WORLD_STRENGTH = 0.08
KEY_SIZE = 0.055

# Detail-study controls. Dimensions and the white/orange boundary remain fixed.
BODY_COLOR_VARIATION = 0.10
BODY_MACRO_ROUGHNESS_VARIATION = 0.035
INLAY_BUMP_STRENGTH = 0.85
INLAY_BUMP_DISTANCE_MM = 0.085
INK_COAT = 0.16
INK_ROUGHNESS_EXTRA = 0.015
INLAY_BLUR_PIXELS = 3.5
INLAY_EDGE_SHADE = 0.55
RESIN_NOISE_CONTRAST = True
FACE_CROWN_MM = 0.045
INK_GROOVE_DEPTH_MM = 0.035
FRONT_EDGE_ROUND_MM = 0.60
RELIEF_GRID_COLUMNS = 161
RELIEF_GRID_ROWS = 241

DETAIL_PRESETS = {
    "baseline": (0.68, 0.52, 0.0, 0.0, 0.24, 0.05, 0.02, 0.075, 0.0, 0.0, False),
    "rounder_edges": (1.00, 0.68, 0.0, 0.0, 0.24, 0.05, 0.02, 0.075, 0.0, 0.0, False),
    "embedded_ink": (1.00, 0.68, 0.0, 0.0, 0.58, 0.06, 0.14, 0.025, 0.0, 0.0, False),
    "stronger_inlay": (1.00, 0.68, 0.0, 0.0, 0.80, 0.085, 0.16, 0.015, 2.5, 0.0, False),
    "resin_variation": (1.00, 0.68, 0.035, 0.018, 0.80, 0.085, 0.16, 0.015, 2.5, 0.0, False),
    "balanced_detail": (1.00, 0.68, 0.06, 0.028, 0.80, 0.085, 0.16, 0.015, 2.5, 0.55, True),
    "visible_study": (1.00, 0.68, 0.25, 0.070, 1.00, 0.100, 0.18, 0.005, 5.0, 1.00, True),
    "final_detail": (1.00, 0.90, 0.10, 0.035, 0.85, 0.085, 0.16, 0.015, 3.5, 0.55, True),
    "rounder_study": (1.40, 0.85, 0.10, 0.035, 0.85, 0.085, 0.16, 0.015, 3.5, 0.55, True),
}


def apply_detail(name):
    global BODY_BEVEL_RADIUS_MM, BASE_BEVEL_RADIUS_MM
    global BODY_COLOR_VARIATION, BODY_MACRO_ROUGHNESS_VARIATION
    global INLAY_BUMP_STRENGTH, INLAY_BUMP_DISTANCE_MM, INK_COAT
    global INK_ROUGHNESS_EXTRA, INLAY_BLUR_PIXELS, INLAY_EDGE_SHADE
    global RESIN_NOISE_CONTRAST
    (BODY_BEVEL_RADIUS_MM, BASE_BEVEL_RADIUS_MM, BODY_COLOR_VARIATION,
     BODY_MACRO_ROUGHNESS_VARIATION, INLAY_BUMP_STRENGTH,
     INLAY_BUMP_DISTANCE_MM, INK_COAT, INK_ROUGHNESS_EXTRA,
     INLAY_BLUR_PIXELS, INLAY_EDGE_SHADE, RESIN_NOISE_CONTRAST) = DETAIL_PRESETS[name]

# Material and lighting variations only. Geometry is shared by every look.
LOOK_PRESETS = {
    "original": (.235, .05, "CC5F5A", "D8A145", .30, .90, .32, .38, -.8, .22, .085),
    "hard_resin": (.19, .11, "B9443F", "C98A2E", .24, 1.10, .20, .38, -.95, .22, .085),
    "amber_contrast": (.18, .12, "B9443F", "D29432", .23, 1.25, .15, .42, -1.05, .22, .085),
    "warm_gloss": (.17, .14, "B5403B", "C98A2E", .21, 1.15, .12, .45, -1.05, .22, .085),
    "soft_photo": (.20, .10, "BB4843", "D29432", .26, 1.05, .19, .32, -.95, .22, .085),
    # A darker shader input compensates for the brightening under AgX and the key light.
    "directional_photo": (.18, .12, "712D2B", "C98A2E", .23, 1.35, .12, .38, -.85, .08, .055),
}


def apply_look(name):
    global BODY_ROUGHNESS, BODY_CLEARCOAT, INK_RED, ORANGE_BASE_COLOR
    global ORANGE_ROUGHNESS, KEY_POWER, FILL_POWER, RIM_POWER, EXPOSURE
    global WORLD_STRENGTH, KEY_SIZE
    (BODY_ROUGHNESS, BODY_CLEARCOAT, INK_RED, ORANGE_BASE_COLOR,
     ORANGE_ROUGHNESS, KEY_POWER, FILL_POWER, RIM_POWER, EXPOSURE,
     WORLD_STRENGTH, KEY_SIZE) = LOOK_PRESETS[name]


def _rgb(value):
    def linear(channel):
        channel = channel / 255.0
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
    return tuple(linear(int(value[i:i + 2], 16)) for i in (0, 2, 4)) + (1.0,)


def _tinted_pair(color, variation):
    base = _rgb(color)
    return (tuple(max(0.0, channel * (1.0 - variation)) for channel in base[:3]) + (1.0,),
            tuple(min(1.0, channel * (1.0 + variation)) for channel in base[:3]) + (1.0,))


def _add_slow_resin_variation(nodes, links, bsdf, base_color, roughness, color_input=None):
    slow_noise = nodes.new("ShaderNodeTexNoise")
    slow_noise.inputs["Scale"].default_value = 5.0
    slow_noise.inputs["Detail"].default_value = 3.0
    low_color, high_color = _tinted_pair(base_color, BODY_COLOR_VARIATION)
    color_mix = nodes.new("ShaderNodeMixRGB")
    color_mix.inputs[1].default_value = low_color
    color_mix.inputs[2].default_value = high_color
    noise_factor = slow_noise.outputs["Fac"]
    if RESIN_NOISE_CONTRAST:
        contrast = nodes.new("ShaderNodeMapRange")
        contrast.inputs["From Min"].default_value = 0.28
        contrast.inputs["From Max"].default_value = 0.72
        links.new(noise_factor, contrast.inputs["Value"])
        noise_factor = contrast.outputs["Result"]
    links.new(noise_factor, color_mix.inputs[0])
    if color_input is not None:
        links.new(color_mix.outputs["Color"], color_input)
    roughness_offset = nodes.new("ShaderNodeMapRange")
    roughness_offset.inputs["To Min"].default_value = -BODY_MACRO_ROUGHNESS_VARIATION
    roughness_offset.inputs["To Max"].default_value = BODY_MACRO_ROUGHNESS_VARIATION
    links.new(noise_factor, roughness_offset.inputs["Value"])
    roughness_sum = nodes.new("ShaderNodeMath")
    roughness_sum.operation = "ADD"
    links.new(roughness, roughness_sum.inputs[0])
    links.new(roughness_offset.outputs["Result"], roughness_sum.inputs[1])
    links.new(roughness_sum.outputs[0], bsdf.inputs["Roughness"])
    return color_mix.outputs["Color"], roughness_sum.outputs[0]


def _blurred_ink_alpha(nodes, links, texture):
    if INLAY_BLUR_PIXELS <= 0.0:
        return texture.outputs["Alpha"]
    coords = nodes.new("ShaderNodeTexCoord")
    image = texture.image
    radius = INLAY_BLUR_PIXELS
    offsets = ((radius / image.size[0], 0.0), (-radius / image.size[0], 0.0),
               (0.0, radius / image.size[1]), (0.0, -radius / image.size[1]))
    alpha = texture.outputs["Alpha"]
    for offset_x, offset_y in offsets:
        shifted_uv = nodes.new("ShaderNodeVectorMath")
        shifted_uv.operation = "ADD"
        shifted_uv.inputs[1].default_value = (offset_x, offset_y, 0.0)
        links.new(coords.outputs["UV"], shifted_uv.inputs[0])
        sample = nodes.new("ShaderNodeTexImage")
        sample.image = image
        sample.interpolation = "Linear"
        links.new(shifted_uv.outputs[0], sample.inputs["Vector"])
        add = nodes.new("ShaderNodeMath")
        add.operation = "ADD"
        links.new(alpha, add.inputs[0])
        links.new(sample.outputs["Alpha"], add.inputs[1])
        alpha = add.outputs[0]
    average = nodes.new("ShaderNodeMath")
    average.operation = "MULTIPLY"
    average.inputs[1].default_value = 0.2
    links.new(alpha, average.inputs[0])
    return average.outputs[0]


def _set_input(bsdf, names, value):
    for name in names:
        socket = bsdf.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def _resin_material(name, color, roughness, specular, ior, clearcoat=0.0):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = _rgb(color)
    bsdf.inputs["Roughness"].default_value = roughness
    _set_input(bsdf, ("Specular IOR Level", "Specular"), specular)
    _set_input(bsdf, ("IOR",), ior)
    _set_input(bsdf, ("Coat Weight", "Clearcoat"), clearcoat)
    _set_input(bsdf, ("Coat Roughness", "Clearcoat Roughness"), 0.18)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 780.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.55
    roughness_map = nodes.new("ShaderNodeMapRange")
    roughness_map.inputs["To Min"].default_value = roughness - 0.018
    roughness_map.inputs["To Max"].default_value = roughness + 0.018
    links.new(noise.outputs["Fac"], roughness_map.inputs["Value"])
    if color == BODY_BASE_COLOR and BODY_COLOR_VARIATION > 0.0:
        _add_slow_resin_variation(nodes, links, bsdf, color,
                                  roughness_map.outputs["Result"], bsdf.inputs["Base Color"])
    else:
        links.new(roughness_map.outputs["Result"], bsdf.inputs["Roughness"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.055
    bump.inputs["Distance"].default_value = 0.000012
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def _backdrop_material(photo_match=False):
    material = bpy.data.materials.new("Soft grey photographic sweep")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = _rgb(BACKGROUND_COLOR)
    bsdf.inputs["Roughness"].default_value = 0.85
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = _rgb(BACKGROUND_COLOR)
    emission.inputs["Strength"].default_value = 2.70 if photo_match else 1.35
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.85 if photo_match else 0.70
    output = nodes.get("Material Output")
    links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    links.new(emission.outputs["Emission"], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs["Surface"])
    return material


def _face_material(texture_path, physical_relief=False):
    material = bpy.data.materials.new("MASTER_TILE_face_inlay")
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = BODY_ROUGHNESS
    _set_input(bsdf, ("IOR",), BODY_IOR)
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = bpy.data.images.load(str(texture_path))
    texture.interpolation = "Linear"
    blurred_alpha = _blurred_ink_alpha(nodes, links, texture)
    separate = nodes.new("ShaderNodeSeparateColor")
    links.new(texture.outputs["Color"], separate.inputs["Color"])
    red_mask = nodes.new("ShaderNodeMath")
    red_mask.operation = "GREATER_THAN"
    red_mask.inputs[1].default_value = 0.08
    links.new(separate.outputs["Red"], red_mask.inputs[0])
    ink = nodes.new("ShaderNodeMixRGB")
    ink.inputs[1].default_value = _rgb(INK_BLACK)
    ink.inputs[2].default_value = _rgb(INK_RED)
    links.new(red_mask.outputs[0], ink.inputs[0])
    surface = nodes.new("ShaderNodeMixRGB")
    surface.inputs[1].default_value = _rgb(BODY_BASE_COLOR)
    if BODY_COLOR_VARIATION > 0.0:
        slow_noise = nodes.new("ShaderNodeTexNoise")
        slow_noise.inputs["Scale"].default_value = 5.0
        slow_noise.inputs["Detail"].default_value = 3.0
        low_color, high_color = _tinted_pair(BODY_BASE_COLOR, BODY_COLOR_VARIATION)
        white_variation = nodes.new("ShaderNodeMixRGB")
        white_variation.inputs[1].default_value = low_color
        white_variation.inputs[2].default_value = high_color
        noise_factor = slow_noise.outputs["Fac"]
        if RESIN_NOISE_CONTRAST:
            contrast = nodes.new("ShaderNodeMapRange")
            contrast.inputs["From Min"].default_value = 0.28
            contrast.inputs["From Max"].default_value = 0.72
            links.new(noise_factor, contrast.inputs["Value"])
            noise_factor = contrast.outputs["Result"]
        links.new(noise_factor, white_variation.inputs[0])
        links.new(white_variation.outputs["Color"], surface.inputs[1])
    links.new(texture.outputs["Alpha"], surface.inputs[0])
    links.new(ink.outputs["Color"], surface.inputs[2])
    face_color = surface.outputs["Color"]
    if INLAY_EDGE_SHADE > 0.0:
        fringe = nodes.new("ShaderNodeMath")
        fringe.operation = "MAXIMUM"
        fringe.inputs[1].default_value = 0.0
        difference = nodes.new("ShaderNodeMath")
        difference.operation = "SUBTRACT"
        links.new(blurred_alpha, difference.inputs[0])
        links.new(texture.outputs["Alpha"], difference.inputs[1])
        links.new(difference.outputs[0], fringe.inputs[0])
        amount = nodes.new("ShaderNodeMath")
        amount.operation = "MULTIPLY"
        amount.inputs[1].default_value = INLAY_EDGE_SHADE * (0.45 if physical_relief else 1.0)
        links.new(fringe.outputs[0], amount.inputs[0])
        edge_tint = nodes.new("ShaderNodeMixRGB")
        edge_tint.inputs[2].default_value = _rgb("938E84")
        links.new(amount.outputs[0], edge_tint.inputs[0])
        links.new(face_color, edge_tint.inputs[1])
        face_color = edge_tint.outputs["Color"]
    links.new(face_color, bsdf.inputs["Base Color"])
    specular = nodes.new("ShaderNodeMapRange")
    specular.inputs["To Min"].default_value = BODY_SPECULAR
    specular.inputs["To Max"].default_value = 0.18
    links.new(texture.outputs["Alpha"], specular.inputs["Value"])
    specular_input = bsdf.inputs.get("Specular IOR Level") or bsdf.inputs.get("Specular")
    links.new(specular.outputs["Result"], specular_input)
    coat = nodes.new("ShaderNodeMapRange")
    coat.inputs["To Min"].default_value = BODY_CLEARCOAT
    coat.inputs["To Max"].default_value = INK_COAT
    links.new(texture.outputs["Alpha"], coat.inputs["Value"])
    coat_input = bsdf.inputs.get("Coat Weight") or bsdf.inputs.get("Clearcoat")
    links.new(coat.outputs["Result"], coat_input)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 780.0
    noise.inputs["Detail"].default_value = 2.0
    resin_roughness = nodes.new("ShaderNodeMapRange")
    resin_roughness.inputs["To Min"].default_value = BODY_ROUGHNESS - 0.012
    resin_roughness.inputs["To Max"].default_value = BODY_ROUGHNESS + 0.012
    links.new(noise.outputs["Fac"], resin_roughness.inputs["Value"])
    ink_roughness = nodes.new("ShaderNodeMath")
    ink_roughness.operation = "MULTIPLY"
    ink_roughness.inputs[1].default_value = INK_ROUGHNESS_EXTRA
    links.new(texture.outputs["Alpha"], ink_roughness.inputs[0])
    roughness = nodes.new("ShaderNodeMath")
    roughness.operation = "ADD"
    links.new(resin_roughness.outputs["Result"], roughness.inputs[0])
    links.new(ink_roughness.outputs[0], roughness.inputs[1])
    if BODY_COLOR_VARIATION > 0.0:
        roughness_offset = nodes.new("ShaderNodeMapRange")
        roughness_offset.inputs["To Min"].default_value = -BODY_MACRO_ROUGHNESS_VARIATION
        roughness_offset.inputs["To Max"].default_value = BODY_MACRO_ROUGHNESS_VARIATION
        links.new(noise_factor, roughness_offset.inputs["Value"])
        roughness_sum = nodes.new("ShaderNodeMath")
        roughness_sum.operation = "ADD"
        links.new(roughness.outputs[0], roughness_sum.inputs[0])
        links.new(roughness_offset.outputs["Result"], roughness_sum.inputs[1])
        links.new(roughness_sum.outputs[0], bsdf.inputs["Roughness"])
    else:
        links.new(roughness.outputs[0], bsdf.inputs["Roughness"])
    inset = nodes.new("ShaderNodeBump")
    inset.invert = True
    inset.inputs["Strength"].default_value = 0.12 if physical_relief else INLAY_BUMP_STRENGTH
    inset.inputs["Distance"].default_value = (0.015 if physical_relief else INLAY_BUMP_DISTANCE_MM) * MM
    links.new(blurred_alpha, inset.inputs["Height"])
    links.new(inset.outputs["Normal"], bsdf.inputs["Normal"])
    return material


def _boundary_points():
    half = BOUNDARY_STEP_WIDTH_MM / 2.0
    center = BOUNDARY_STEP_OFFSET_MM
    shoulder = BOUNDARY_STEP_SHOULDER_MM
    return [center - half - shoulder, center - half, center + half,
            center + half + shoulder]


def _boundary_height(y, right_side):
    if not BOUNDARY_STEP_ENABLED or not right_side:
        return VISIBLE_ORANGE_HEIGHT_MM
    start, inner_start, inner_end, end = _boundary_points()
    if y <= start or y >= end:
        return VISIBLE_ORANGE_HEIGHT_MM
    if inner_start <= y <= inner_end:
        return VISIBLE_ORANGE_HEIGHT_MM - BOUNDARY_STEP_DEPTH_MM
    if y < inner_start:
        return VISIBLE_ORANGE_HEIGHT_MM - BOUNDARY_STEP_DEPTH_MM * (y - start) / (inner_start - start)
    return VISIBLE_ORANGE_HEIGHT_MM - BOUNDARY_STEP_DEPTH_MM * (end - y) / (end - inner_end)


def _outline(radius_mm):
    half_width = TILE_WIDTH_MM / 2.0
    half_height = TILE_HEIGHT_MM / 2.0
    radius = min(radius_mm, half_width, half_height)
    corner_steps = BEVEL_SEGMENTS
    points = [(-half_width + radius, -half_height),
              (half_width - radius, -half_height)]
    for index in range(1, corner_steps + 1):
        angle = -math.pi / 2.0 + math.pi * index / (2.0 * corner_steps)
        points.append((half_width - radius + radius * math.cos(angle),
                       -half_height + radius + radius * math.sin(angle)))
    points.extend((half_width, y) for y in _boundary_points())
    points.append((half_width, half_height - radius))
    for index in range(1, corner_steps + 1):
        angle = math.pi * index / (2.0 * corner_steps)
        points.append((half_width - radius + radius * math.cos(angle),
                       half_height - radius + radius * math.sin(angle)))
    points.append((-half_width + radius, half_height))
    for index in range(1, corner_steps + 1):
        angle = math.pi / 2.0 + math.pi * index / (2.0 * corner_steps)
        points.append((-half_width + radius + radius * math.cos(angle),
                       half_height - radius + radius * math.sin(angle)))
    points.append((-half_width, -half_height + radius))
    for index in range(1, corner_steps):
        angle = math.pi + math.pi * index / (2.0 * corner_steps)
        points.append((-half_width + radius + radius * math.cos(angle),
                       -half_height + radius + radius * math.sin(angle)))
    return points


def _layer_mesh(name, lower_z, upper_z, lower_scale, upper_scale, corner_radius_mm,
                lower_is_boundary=False, upper_is_boundary=False, front_lip_mm=0.0):
    outline = _outline(corner_radius_mm)
    count = len(outline)
    rings = [(lower_z, lower_scale, lower_is_boundary, 0.0)]
    if front_lip_mm > 0.0:
        lip = min(front_lip_mm, (upper_z - lower_z) / 4.0)
        rings.append((upper_z - lip, upper_scale, False, 0.0))
        for index in range(1, 5):
            angle = math.pi * index / 8.0
            rings.append((upper_z - lip + lip * math.sin(angle), upper_scale,
                          False, lip * (1.0 - math.cos(angle))))
    else:
        rings.append((upper_z, upper_scale, upper_is_boundary, 0.0))
    vertices = []
    for z, scale, stepped, inset in rings:
        x_shrink = 1.0 - inset / (TILE_WIDTH_MM / 2.0)
        y_shrink = 1.0 - inset / (TILE_HEIGHT_MM / 2.0)
        for x, y in outline:
            edge_z = _boundary_height(y, x > 0) if stepped else z
            vertices.append((x * scale * x_shrink * MM,
                             y * scale * y_shrink * MM, edge_z * MM))
    lower_center, upper_center = len(vertices), len(vertices) + 1
    vertices.extend([(0.0, 0.0, lower_z * MM), (0.0, 0.0, upper_z * MM)])
    faces, top_faces, smooth_faces = [], [], []
    for index in range(count):
        following = (index + 1) % count
        faces.append((lower_center, following, index))
    for ring_index in range(len(rings) - 1):
        lower_start = ring_index * count
        upper_start = (ring_index + 1) * count
        for index in range(count):
            following = (index + 1) % count
            smooth_faces.append(len(faces))
            faces.append((lower_start + index, lower_start + following,
                          upper_start + following, upper_start + index))
    top_start = (len(rings) - 1) * count
    for index in range(count):
        following = (index + 1) % count
        top_faces.append(len(faces))
        faces.append((upper_center, top_start + index, top_start + following))
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for face_index in smooth_faces:
        mesh.polygons[face_index].use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj, top_faces


def _add_bevel(obj, radius_mm, name):
    # The silhouette radius lives in the mesh; this modifier only softens the face lip.
    bevel = obj.modifiers.new(name + " edge lip", "BEVEL")
    bevel.width = min(radius_mm * 0.3, 0.30) * MM
    bevel.segments = BEVEL_SEGMENTS
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(20.0)
    bevel.use_clamp_overlap = True
    bevel.harden_normals = True
    normal = obj.modifiers.new("Continuous moulded reflections", "WEIGHTED_NORMAL")
    normal.keep_sharp = True
    normal.weight = 50


def _create_face_relief(texture_path, body_front_z):
    image = bpy.data.images.load(str(texture_path))
    width, height = image.size
    pixels = array("f", [0.0]) * (width * height * 4)
    image.pixels.foreach_get(pixels)

    def alpha_at(u, v):
        px = max(0.0, min(width - 1.0, u * (width - 1)))
        py = max(0.0, min(height - 1.0, v * (height - 1)))
        x0, y0 = int(px), int(py)
        x1, y1 = min(x0 + 1, width - 1), min(y0 + 1, height - 1)
        dx, dy = px - x0, py - y0
        def value(x, y):
            return pixels[4 * (y * width + x) + 3]
        low = value(x0, y0) * (1.0 - dx) + value(x1, y0) * dx
        high = value(x0, y1) * (1.0 - dx) + value(x1, y1) * dx
        return low * (1.0 - dy) + high * dy

    half_x, half_y = 8.8, 13.1
    columns, rows = RELIEF_GRID_COLUMNS, RELIEF_GRID_ROWS
    vertices = []
    for row in range(rows):
        y = -half_y + 2.0 * half_y * row / (rows - 1)
        for column in range(columns):
            x = -half_x + 2.0 * half_x * column / (columns - 1)
            edge_distance = min(half_x - abs(x), half_y - abs(y))
            edge_weight = min(1.0, max(0.0, edge_distance / 0.55))
            edge_weight = edge_weight * edge_weight * (3.0 - 2.0 * edge_weight)
            crown_weight = 0.02 + 0.98 * edge_weight
            u = x / TILE_WIDTH_MM + 0.5
            v = y / TILE_HEIGHT_MM + 0.5
            z = body_front_z + FACE_CROWN_MM * crown_weight
            z -= INK_GROOVE_DEPTH_MM * alpha_at(u, v) * edge_weight
            vertices.append((x * MM, y * MM, z * MM))
    faces = []
    for row in range(rows - 1):
        for column in range(columns - 1):
            index = row * columns + column
            faces.append((index, index + 1, index + columns + 1, index + columns))
    mesh = bpy.data.meshes.new("MASTER_TILE_face_relief_mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    part = bpy.data.objects.new("MASTER_TILE_face_relief", mesh)
    bpy.context.collection.objects.link(part)
    part.data.materials.append(_face_material(texture_path, physical_relief=True))
    uv_layer = mesh.uv_layers.new(name="Face UV")
    for polygon in mesh.polygons:
        polygon.use_smooth = True
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv_layer.data[loop_index].uv = (
                vertex.x / (TILE_WIDTH_MM * MM) + 0.5,
                vertex.y / (TILE_HEIGHT_MM * MM) + 0.5,
            )
    part["master_tile"] = True
    part["physical_ink_depth_mm"] = INK_GROOVE_DEPTH_MM
    return part


def create_master_tile(texture_path, pose="upright", relief="geometry"):
    interface_scale = 1.0 - TAPER_RATIO * (1.0 - VISIBLE_ORANGE_HEIGHT_MM / TILE_DEPTH_MM)
    back_scale = 1.0 - TAPER_RATIO
    body_front_z = TILE_DEPTH_MM - FACE_CROWN_MM if relief == "geometry" else TILE_DEPTH_MM
    orange, _ = _layer_mesh(
        "MASTER_TILE_orange", 0.0, VISIBLE_ORANGE_HEIGHT_MM,
        back_scale, interface_scale, BASE_BEVEL_RADIUS_MM, upper_is_boundary=True)
    orange.data.materials.append(_resin_material(
        "Orange ochre resin", ORANGE_BASE_COLOR, ORANGE_ROUGHNESS,
        ORANGE_SPECULAR, ORANGE_IOR))
    _add_bevel(orange, BASE_BEVEL_RADIUS_MM, "Rounded orange shell")

    body, top_faces = _layer_mesh(
        "MASTER_TILE_ivory", VISIBLE_ORANGE_HEIGHT_MM, body_front_z,
        interface_scale, 1.0, BODY_BEVEL_RADIUS_MM, lower_is_boundary=True,
        front_lip_mm=FRONT_EDGE_ROUND_MM if relief == "geometry" else 0.0)
    body.data.materials.append(_resin_material(
        "Warm ivory resin", BODY_BASE_COLOR, BODY_ROUGHNESS,
        BODY_SPECULAR, BODY_IOR, BODY_CLEARCOAT))
    if relief == "shader":
        body.data.materials.append(_face_material(texture_path))
        uv_layer = body.data.uv_layers.new(name="Face UV")
        for face_index in top_faces:
            polygon = body.data.polygons[face_index]
            polygon.material_index = 1
            for loop_index in polygon.loop_indices:
                vertex = body.data.vertices[body.data.loops[loop_index].vertex_index].co
                uv_layer.data[loop_index].uv = (
                    vertex.x / (TILE_WIDTH_MM * MM) + 0.5,
                    vertex.y / (TILE_HEIGHT_MM * MM) + 0.5,
                )
    _add_bevel(body, BODY_BEVEL_RADIUS_MM, "Rounded ivory shell")
    parts = [body, orange]
    if relief == "geometry":
        parts.append(_create_face_relief(texture_path, body_front_z))
    for part in parts:
        if pose == "lying":
            part.rotation_euler.x = 0.0
            part.location.z = 0.0
        else:
            part.rotation_euler.x = math.radians(90.0)
            part.location.z = TILE_HEIGHT_MM * MM / 2.0
    body["master_tile"] = orange["master_tile"] = True
    return body, orange


def _look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def _area_light(name, location, energy, size, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = location
    _look_at(light, (0.0, -0.008, 0.014))


def _create_seamless_sweep(photo_match=False):
    rows = [(-1.0, -0.0008), (0.12, -0.0008)]
    radius = 0.12
    for index in range(1, 17):
        angle = (math.pi / 2.0) * index / 16.0
        rows.append((0.12 + radius * math.sin(angle),
                     -0.0008 + radius * (1.0 - math.cos(angle))))
    rows.append((0.24, 1.0))
    vertices = [(-1.0, y, z) for y, z in rows] + [(1.0, y, z) for y, z in rows]
    row_count = len(rows)
    faces = [(index, row_count + index, row_count + index + 1, index + 1)
             for index in range(row_count - 1)]
    mesh = bpy.data.meshes.new("Seamless sweep mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    sweep = bpy.data.objects.new("Seamless light-grey sweep", mesh)
    bpy.context.collection.objects.link(sweep)
    sweep.data.materials.append(_backdrop_material(photo_match))
    for polygon in sweep.data.polygons:
        polygon.use_smooth = True
    return sweep


def setup_product_scene(samples=RENDER_SAMPLES, size=RENDER_SIZE, pose="upright"):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "MILLIMETERS"
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = EXPOSURE
    world = scene.world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = _rgb(BACKGROUND_COLOR)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = WORLD_STRENGTH
    _create_seamless_sweep(pose == "lying")
    _area_light("Key softbox", (-0.075, -0.095, 0.13), KEY_POWER, KEY_SIZE, (1.0, 0.95, 0.89))
    fill_color = (0.98, 0.96, 0.92) if pose == "lying" else (0.91, 0.95, 1.0)
    fill_power = max(FILL_POWER, 0.15) if pose == "lying" else FILL_POWER
    _area_light("Fill softbox", (0.095, -0.070, 0.080), fill_power, 0.075, fill_color)
    _area_light("Top rim strip", (0.015, 0.075, 0.11), RIM_POWER, 0.070, (1.0, 0.98, 0.95))


def _camera(name, location, lens, target):
    data = bpy.data.cameras.new(name)
    data.lens, data.sensor_width = lens, 36.0
    data.clip_start = 0.001
    data.dof.use_dof = False
    data.dof.focus_distance = (Vector(location) - Vector(target)).length
    data.dof.aperture_fstop = 22.0
    camera = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(camera)
    camera.location = location
    _look_at(camera, target)
    return camera


def render_views(output_dir, only="all", pose="upright"):
    scene = bpy.context.scene
    output_dir.mkdir(parents=True, exist_ok=True)
    if pose == "lying":
        views = (("master_photo_match.png", (0.048, -0.066, 0.072), 90.0,
                  (0.0, 0.0, 0.009)),)
    else:
        views = (
            ("master_front.png", (0.008, -0.120, 0.047), 95.0, (0.0, -0.008, 0.014)),
            ("master_angled.png", (0.070, -0.120, 0.055), 90.0, (0.0, -0.007, 0.014)),
            ("master_orange_detail.png", (0.080, -0.105, 0.034), 100.0, (0.0, -0.006, 0.014)),
        )
    for filename, location, lens, target in views:
        if only != "all" and only not in filename:
            if only == "front_angle" and filename != "master_orange_detail.png":
                pass
            else:
                continue
        scene.camera = _camera("Camera_" + filename, location, lens, target)
        scene.render.filepath = str(output_dir / filename)
        bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--texture", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=RENDER_SAMPLES)
    parser.add_argument("--size", type=int, default=RENDER_SIZE)
    parser.add_argument("--only", choices=("all", "front", "angled", "orange_detail", "front_angle", "photo"), default="all")
    parser.add_argument("--look", choices=LOOK_PRESETS, default="directional_photo")
    parser.add_argument("--detail", choices=DETAIL_PRESETS, default="final_detail")
    parser.add_argument("--pose", choices=("upright", "lying"), default="upright")
    parser.add_argument("--relief", choices=("shader", "geometry"), default="geometry")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(argv)
    apply_look(args.look)
    apply_detail(args.detail)
    setup_product_scene(args.samples, args.size, args.pose)
    create_master_tile(args.texture.resolve(), args.pose, args.relief)
    render_views(args.output.resolve(), args.only, args.pose)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output / "master_tile.blend").resolve()))


if __name__ == "__main__":
    main()
