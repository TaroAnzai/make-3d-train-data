from PIL import Image

from make_3d_train_data.texture_generator import generate_textures


def test_textures_use_bundled_regular_artwork(tmp_path):
    textures = generate_textures(tmp_path)

    assert len(textures) == 37
    with Image.open(tmp_path / "1m.png") as texture:
        assert texture.mode == "RGBA"
        assert texture.size == (600, 800)

    with Image.open(tmp_path / "red5s.png") as texture:
        assert texture.getextrema()[3] == (0, 255)
