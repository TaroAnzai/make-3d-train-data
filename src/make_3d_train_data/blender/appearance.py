"""Small per-render material changes and a rare fingertip occluder."""

import bpy


def _principled(material):
    return next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")


def _set_specular(shader, value):
    name = "Specular IOR Level" if "Specular IOR Level" in shader.inputs else "Specular"
    shader.inputs[name].default_value = value


def vary_tiles(objects, appearance):
    # The master mesh is shared; assign object-linked copies so its materials stay intact.
    copies = {}
    for obj, _ in objects:
        for slot in obj.material_slots:
            source = slot.material
            if source is None:
                continue
            if source.name not in copies:
                material = source.copy()
                material.name = source.name + "_varied"
                shader = _principled(material)
                shader.inputs["Roughness"].default_value = appearance["tile_roughness"]
                _set_specular(shader, appearance["tile_specular"])
                copies[source.name] = material
            slot.link = "OBJECT"
            slot.material = copies[source.name]


def vary_felt(appearance):
    mat = bpy.data.objects["mat_table"]
    for slot in mat.material_slots:
        source = slot.material
        if source is None or "felt" not in source.name.lower():
            continue
        material = source.copy()
        material.name = source.name + "_varied"
        slot.link = "OBJECT"
        slot.material = material
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        shader = _principled(material)
        shader.inputs["Roughness"].default_value = appearance["felt_roughness"]

        original = shader.inputs["Base Color"].links[0].from_socket
        tint = nodes.new("ShaderNodeMixRGB")
        tint.blend_type = "MULTIPLY"
        tint.inputs[0].default_value = 1
        tint.inputs[2].default_value = (*[v * appearance["felt_brightness"] for v in appearance["felt_tint"]], 1)
        links.new(original, tint.inputs[1])

        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 180
        ramp = nodes.new("ShaderNodeValToRGB")
        strength = appearance["felt_texture_strength"]
        ramp.color_ramp.elements[0].color = (1 - strength, 1 - strength, 1 - strength, 1)
        ramp.color_ramp.elements[1].color = (1 + strength, 1 + strength, 1 + strength, 1)
        links.new(noise.outputs["Fac"], ramp.inputs[0])
        variation = nodes.new("ShaderNodeMixRGB")
        variation.blend_type = "MULTIPLY"
        variation.inputs[0].default_value = 1
        links.new(tint.outputs[0], variation.inputs[1])
        links.new(ramp.outputs[0], variation.inputs[2])
        links.new(variation.outputs[0], shader.inputs["Base Color"])

        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .09
        bump.inputs["Distance"].default_value = .0003
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])


def create_fingertip(desc, surface_z):
    # One rounded fingertip touches the outer edge of a single hand tile.
    upright = desc["rotation_x"] > 45
    x = desc["x"] + desc["side"] * .011
    y = desc["y"] - (.010 if upright else .013)
    z = surface_z + (.026 if upright else .010)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=(x, y, z))
    finger = bpy.context.object
    finger.name = "light_fingertip_occlusion"
    finger.scale = (.006, .014, .005)
    material = bpy.data.materials.new("natural_skin")
    material.use_nodes = True
    shader = _principled(material)
    shader.inputs["Base Color"].default_value = (.62, .35, .25, 1)
    shader.inputs["Roughness"].default_value = .68
    finger.data.materials.append(material)
