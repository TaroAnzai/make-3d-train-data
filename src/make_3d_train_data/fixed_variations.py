"""Seeded variations of a tagged fixed mahjong-table layout."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import random

from .class_defs import CLASSES


def _signed_magnitude(rng: random.Random, values: list[float]) -> float:
    magnitude = rng.uniform(*values)
    return magnitude if rng.randrange(2) else -magnitude


def _maybe_range(rng: random.Random, values: list[float], baseline: float, probability: float) -> float:
    return rng.uniform(*values) if rng.random() < probability else baseline


def balanced_hand_classes(seed: int, index: int, counts: list[int]) -> list[str]:
    """Draw without replacement from shuffled 37-class decks."""
    return list(_balanced_hands(seed, tuple(counts))[index])


@lru_cache(maxsize=8)
def _balanced_hands(seed: int, counts: tuple[int, ...]) -> tuple[tuple[str, ...], ...]:
    rng = random.Random(seed)
    names = [cls.name for cls in CLASSES]
    deck: list[str] = []
    cursor = 0
    hands = []
    for count in counts:
        hand: list[str] = []
        while len(hand) < count:
            if cursor == len(deck):
                deck = names.copy()
                rng.shuffle(deck)
                # A hand crossing a deck boundary still has distinct classes.
                needed = count - len(hand)
                while set(deck[:needed]) & set(hand):
                    rng.shuffle(deck)
                cursor = 0
            take = min(count - len(hand), len(deck) - cursor)
            hand.extend(deck[cursor:cursor + take])
            cursor += take
        rng.shuffle(hand)
        hands.append(tuple(hand))
    return tuple(hands)


def vary_fixed_scene(config: dict, index: int, rng: random.Random) -> tuple[list[dict], dict, dict, dict]:
    spec = config["variations"]
    p3, p2 = spec["star3_probability"], spec["star2_probability"]
    tiles = deepcopy(config["tiles_fixed"])
    camera = deepcopy(config["scene"]["camera"])
    lighting = deepcopy(config["scene"]["lighting"])
    noise = deepcopy(config["noise"])

    hand = [tile for tile in tiles if tile.get("group") == "hand"]
    hand_spec = spec["hand"]
    counts = [hand_spec["count_options"][i % len(hand_spec["count_options"])]
              for i in range(max(index + 1, config["output"]["count"]))]
    count = counts[index]
    classes = balanced_hand_classes(config["general"]["seed"], index, counts)
    spacing = rng.uniform(*hand_spec["spacing_mm_range"]) / 1000
    # A wider 14-tile hand is kept within approximately the same frame width.
    if count == 14:
        spacing = min(spacing, 0.021)
    center_x = sum(tile["x"] for tile in hand) / len(hand)
    center_y = sum(tile["y"] for tile in hand) / len(hand)
    x_offset = _signed_magnitude(rng, hand_spec["x_offset_mm_range"]) / 1000
    y_offset = _signed_magnitude(rng, hand_spec["y_offset_mm_range"]) / 1000
    hand_rotation_x = 0 if rng.random() < hand_spec["face_up_probability"] else 90
    for slot in range(count):
        tile = deepcopy(hand[min(slot, len(hand) - 1)])
        tile["class"] = classes[slot]
        tile["rotation_x"] = hand_rotation_x
        tile["x"] = round(center_x + (slot - (count - 1) / 2) * spacing + x_offset, 6)
        tile["y"] = round(center_y + y_offset, 6)
        tile["rotation_z"] = round(_signed_magnitude(rng, hand_spec["rotation_z_deg_range"]), 4)
        if slot < len(hand):
            hand[slot].update(tile)
        else:
            tiles.insert(len(hand), tile)
    if count < len(hand):
        removed = hand[count:]
        tiles = [tile for tile in tiles if all(tile is not old for old in removed)]

    # Star 4: camera distance and tilt change for every image.
    camera["distance_range"] = spec["camera"]["distance_range"]
    camera["tilt_deg_range"] = spec["camera"]["tilt_deg_range"]
    camera["lens_mm"] = spec["camera"]["lens_mm"]
    # Star 3: each parameter independently retains its reference value 20% of the time.
    for key in ("yaw_deg_range", "roll_deg_range"):
        if rng.random() < p3:
            camera[key] = spec["camera"][key]
    for key in ("target_x", "target_y"):
        camera[key] = _maybe_range(rng, spec["camera"][key + "_range"], camera[key], p3)
    lighting["intensity_range"] = (
        spec["lighting"]["intensity_range"] if rng.random() < p3 else lighting["intensity_range"]
    )
    for key in ("brightness_range", "contrast_range"):
        if rng.random() < p3:
            noise[key] = spec["noise"][key]
    if rng.random() < p2:
        noise["jpeg_quality_range"] = spec["noise"]["jpeg_quality_range"]
    # Half the images are eligible for blur; the conditional rate comes from YAML.
    noise["blur_prob"] = spec["noise"]["blur_conditional_probability"] if rng.random() < p2 else 0
    noise["blur_sigma_range"] = spec["noise"]["blur_sigma_range"]

    # Star 2: change discarded tiles and wall structure independently.
    if rng.random() < p2:
        discards = [tile for tile in tiles if tile.get("group") == "discard"]
        for tile in discards:
            tile["class"] = rng.choice(CLASSES).name
        removed = rng.sample(discards, rng.randint(1, spec["discard_max_removed"]))
        tiles = [tile for tile in tiles if all(tile is not old for old in removed)]
    if rng.random() < p2:
        for group in ("wall_front", "wall_back", "wall_right"):
            wall = [tile for tile in tiles if tile.get("group") == group]
            dx = _signed_magnitude(rng, spec["wall_shift_mm_range"]) / 1000
            dy = _signed_magnitude(rng, spec["wall_shift_mm_range"]) / 1000
            for tile in wall:
                tile["x"] = round(tile["x"] + dx, 6)
                tile["y"] = round(tile["y"] + dy, 6)
        # Remove complete end columns so the remaining two-layer wall stays supported.
        back = [tile for tile in tiles if tile.get("group") == "wall_back"]
        columns = sorted({tile["x"] for tile in back})
        end = rng.choice(("left", "right"))
        width = rng.randint(1, spec["wall_max_removed"])
        removed_x = set(columns[:width] if end == "left" else columns[-width:])
        tiles = [tile for tile in tiles
                 if not (tile.get("group") == "wall_back" and tile["x"] in removed_x)]

    return tiles, camera, lighting, noise
