from tge_rdn_scraper.scheduler import TGEScheduler


def test_default_run_times_are_fixed_twice_daily():
    assert TGEScheduler.get_default_run_times() == ["00:01", "12:01"]


def test_custom_run_times_are_comma_separated():
    assert TGEScheduler.get_run_times("06:30, 18:45") == ["06:30", "18:45"]


def test_legacy_wildcard_uses_default_run_times():
    assert TGEScheduler.get_run_times("*") == ["00:01", "12:01"]
