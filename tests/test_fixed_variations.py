from collections import Counter

from make_3d_train_data.config import load_config
from make_3d_train_data.scene_generator import generate_scene, generate_scenes


def test_photo_variations_balance_hand_across_100_images():
    cfg = load_config("configs/photo_34344494.yaml")
    scenes = generate_scenes(cfg, 100)
    hands = [[tile for tile in scene.tiles if tile.annotate] for scene in scenes]
    assert [len(hand) for hand in hands] == [13, 14] * 50
    frequencies = Counter(tile.class_name for hand in hands for tile in hand)
    assert len(frequencies) == 37
    assert max(frequencies.values()) - min(frequencies.values()) <= 1
    assert len({tuple(tile.class_name for tile in hand) for hand in hands}) == 100
    assert all(0.48 <= scene.camera.distance <= 0.54 for scene in scenes)
    assert all(50 <= scene.camera.tilt_deg <= 62 for scene in scenes)
    assert all(sum(tile.annotate for tile in scene.tiles) == len(hand)
               for scene, hand in zip(scenes, hands))
    assert {hand[0].rotation_x for hand in hands} == {0, 90}
    assert all({tile.rotation_x for tile in hand} == {hand[0].rotation_x} for hand in hands)
    assert all(not tile.face_down for hand in hands for tile in hand)
    assert len({scene.lighting.key_position for scene in scenes}) == 100
    assert len({scene.lighting.fill_position for scene in scenes}) == 100
    assert len({scene.lighting.color_temperature for scene in scenes}) == 100
    assert len({scene.appearance["tile_roughness"] for scene in scenes}) == 100
    assert len({scene.appearance["felt_tint"][1] for scene in scenes}) == 100
    assert all(.34 <= scene.appearance["tile_roughness"] <= .48 for scene in scenes)
    assert all(.30 <= scene.appearance["tile_specular"] <= .42 for scene in scenes)


def test_photo_variations_reproducible_and_preserve_indicator():
    cfg = load_config("configs/photo_34344494.yaml")
    first = generate_scene(cfg, 7)
    assert first.to_dict() == generate_scene(cfg, 7).to_dict()
    assert any(tile.class_name == "1s" and tile.z == 0.0165
               and tile.rotation_x == 0 for tile in first.tiles)
    assert 13 <= sum(tile.annotate for tile in first.tiles) <= 14


def test_photo_occlusion_can_be_enabled_without_changing_labels():
    cfg = load_config("configs/photo_34344494.yaml")
    cfg["variations"]["hand_occlusion_probability"] = 1
    scene = generate_scene(cfg, 0)
    assert scene.occlusion["kind"] == "fingertip"
    assert any(tile.annotate and tile.x == scene.occlusion["x"] for tile in scene.tiles)
    assert scene.to_dict() == generate_scene(cfg, 0).to_dict()
