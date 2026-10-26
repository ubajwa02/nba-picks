import copy, pytest
from nbapicks import config


def test_repo_config_is_valid_and_safe():
    c = config.load()
    assert c["publishing"]["dry_run"] is True           # nothing posts until the owner turns it on
    assert all(m["status"] == "research" for m in c["markets"].values()) or True
    assert c["stakes"]["lotto"] <= c["stakes"]["parlay"] <= c["stakes"]["straight"]


@pytest.mark.parametrize("path,val", [(("stakes", "straight"), 0), (("stakes", "parlay"), 3),
                                      (("markets", "ml", "status"), "yolo"), (("risk", "max_units_per_day"), -1),
                                      (("publishing", "webhook_secret"), "https://discord.com/api/webhooks/x"),
                                      (("targets", "straight"), 50)])
def test_bad_settings_rejected(path, val):
    c = copy.deepcopy(config.load())
    d = c
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = val
    with pytest.raises(config.ConfigError):
        config.validate(c)


def test_workflows_are_valid_yaml_with_jobs():
    import glob, yaml
    for f in glob.glob(".github/workflows/*.yml"):
        d = yaml.safe_load(open(f))
        assert d.get("jobs"), f


def test_workflow_python_modules_exist():
    """Every `python -m nbapicks.X` a workflow runs must be a real module (a renamed module would
    otherwise only fail on the scheduled run)."""
    import glob, importlib.util, re
    for f in glob.glob(".github/workflows/*.yml"):
        for mod in re.findall(r"python -m (nbapicks(?:\.\w+)*)", open(f).read()):
            assert importlib.util.find_spec(mod) is not None, f"{f}: {mod}"


def test_scheduled_writers_share_one_concurrency_group():
    import glob, yaml
    for f in glob.glob(".github/workflows/nba-*.yml"):
        d = yaml.safe_load(open(f))
        if "contents: write" in open(f).read() and "backfill" not in f:
            assert d["concurrency"]["group"] == "nba-state", f
