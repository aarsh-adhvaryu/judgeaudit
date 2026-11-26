import yaml

from judgeaudit.cli import main


def write_cfg(tmp_path, make_cfg, **judge):
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(make_cfg(**judge)), encoding="utf-8")
    return str(path)


def test_run_and_gate(tmp_path, make_cfg, capsys):
    clean = write_cfg(tmp_path, make_cfg)
    assert main(["run", "-c", clean, "--gate"]) == 0
    biased = write_cfg(tmp_path, make_cfg, injection_susceptibility=1.0)
    assert main(["run", "-c", biased]) == 0
    assert main(["run", "-c", biased, "--gate"]) == 1
    assert "NOT TRUSTED" in capsys.readouterr().out


def test_report_can_be_rebuilt_with_the_same_verdict(tmp_path, make_cfg):
    cfg_path = write_cfg(tmp_path, make_cfg, position_bias=1.0)
    main(["run", "-c", cfg_path])
    run_dir = str(tmp_path / "runs" / "t")
    assert main(["report", run_dir, "--gate"]) == 1


def test_bad_config_is_a_clean_error(tmp_path, capsys):
    path = tmp_path / "bad.yaml"
    path.write_text("run_name: x\n", encoding="utf-8")
    assert main(["run", "-c", str(path)]) == 2
    assert "missing required key" in capsys.readouterr().err
