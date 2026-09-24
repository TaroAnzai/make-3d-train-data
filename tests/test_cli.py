from unittest.mock import patch

from make_3d_train_data.cli import main


def test_generate_count_overrides_config(capsys):
    with patch("make_3d_train_data.cli.build_dataset", return_value="output/dataset") as build:
        assert main(["generate", "--config", "configs/fixed_sample.yaml", "--count", "3"]) == 0
    assert build.call_args.args[0]["output"]["count"] == 3
    assert "Dataset generated" in capsys.readouterr().out


def test_generate_uses_config_count_by_default():
    with patch("make_3d_train_data.cli.build_dataset", return_value="output/dataset") as build:
        assert main(["generate", "--config", "configs/default_random.yaml"]) == 0
    assert build.call_args.args[0]["output"]["count"] == 3000


def test_generate_rejects_nonpositive_count(capsys):
    with patch("make_3d_train_data.cli.build_dataset") as build:
        assert main(["generate", "--config", "configs/fixed_sample.yaml", "--count", "0"]) == 2
    build.assert_not_called()
    assert "--count must be a positive integer" in capsys.readouterr().err
