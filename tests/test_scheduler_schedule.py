from tge_rdn_scraper.scheduler import TGEScheduler


def test_default_run_times_are_fixed_twice_daily():
    assert TGEScheduler.get_default_run_times() == ["00:01", "12:01"]
