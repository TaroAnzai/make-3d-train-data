from make_3d_train_data.config import load_config
from make_3d_train_data.scene_generator import generate_scene
def test_seed_reproducible():
    cfg=load_config("configs/default_random.yaml"); assert generate_scene(cfg,3).to_dict()==generate_scene(cfg,3).to_dict()
def test_seed_changes():
    cfg=load_config("configs/default_random.yaml"); assert generate_scene(cfg,0).to_dict()!=generate_scene(cfg,1).to_dict()
def test_fixed_tiles():
    scene=generate_scene(load_config("configs/fixed_sample.yaml")); assert [x.class_name for x in scene.tiles]==["1m","east","red5p"]
