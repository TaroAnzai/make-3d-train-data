import pytest
from make_3d_train_data.config import load_config,validate_config,DEFAULTS
def test_load_default(): assert load_config("configs/default.yaml")["output"]["count"] > 0
def test_fixed_config(): assert load_config("configs/fixed_sample.yaml")["scene"]["mode"]=="fixed"
def test_invalid_mode():
    import copy
    cfg=copy.deepcopy(DEFAULTS); cfg["scene"]["mode"]="bad"
    with pytest.raises(ValueError): validate_config(cfg)
