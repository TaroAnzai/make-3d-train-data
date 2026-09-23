import math

import bpy
from mathutils import Euler, Vector


# Physical proportions in millimetres. Blender uses a uniform model scale below,
# so these values can be tuned directly against measurements of a real tile.
TILE_HEIGHT = 28.0
TILE_WIDTH = 21.0
TILE_DEPTH = 17.5
ORANGE_DEPTH_RATIO = 0.20
BEVEL_RADIUS = 0.6
TAPER_RATIO = 0.015

_MODEL_SCALE = 1.0 / 14.0


def _ring(width, height, z):
    x = width / 2.0
    y = height / 2.0
    return [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]


def _tile_mesh(scale):
    width = TILE_WIDTH * _MODEL_SCALE * scale
    height = TILE_HEIGHT * _MODEL_SCALE * scale
    depth = TILE_DEPTH * _MODEL_SCALE * scale
    orange_depth = depth * ORANGE_DEPTH_RATIO

    back_width = width * (1.0 - TAPER_RATIO)
    back_height = height * (1.0 - TAPER_RATIO)
    boundary_width = back_width + (width - back_width) * ORANGE_DEPTH_RATIO
    boundary_height = back_height + (height - back_height) * ORANGE_DEPTH_RATIO

    z_back = -depth / 2.0
    z_boundary = z_back + orange_depth
    z_front = depth / 2.0
    vertices = (
        _ring(back_width, back_height, z_back)
        + _ring(boundary_width, boundary_height, z_boundary)
        + _ring(width, height, z_front)
    )

    # Material slots: 0=ivory body, 1=textured face, 2=orange back.
    faces = [(0, 3, 2, 1), (8, 9, 10, 11)]
    material_indices = [2, 1]
    for ring_start, material_index in ((0, 2), (4, 0)):
        next_ring = ring_start + 4
        for corner in range(4):
            following = (corner + 1) % 4
            faces.append(
                (
                    ring_start + corner,
                    ring_start + following,
                    next_ring + following,
                    next_ring + corner,
                )
            )
            material_indices.append(material_index)
    half = Vector((width / 2.0, height / 2.0, depth / 2.0))
    return vertices, faces, material_indices, half


def create_tile(tile):
    scale = tile["scale"]
    vertices, faces, material_indices, half = _tile_mesh(scale)
    mesh = bpy.data.meshes.new(f"tile_mesh_{tile['class_id']}_{tile['class_name']}")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index

    rotation = Euler(
        [math.radians(tile[key]) for key in ("rotation_x", "rotation_y", "rotation_z")],
        "XYZ",
    )
    vertical_extent = sum(abs(rotation.to_matrix()[2][axis]) * half[axis] for axis in range(3))
    obj = bpy.data.objects.new(f"tile_{tile['class_id']}_{tile['class_name']}", mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = (tile["x"], tile["y"], tile["z"] + vertical_extent)
    obj.rotation_euler = rotation
    obj["layered_tile_materials"] = True

    bevel = obj.modifiers.new("Moulded rounded edges", "BEVEL")
    bevel.width = BEVEL_RADIUS * _MODEL_SCALE * scale
    bevel.segments = 5
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(10.0)
    return obj
