import pytest
from pathlib import Path
import cProfile
import pstats
from io import StringIO


THIS_DIR = Path(__file__).parent.resolve()


def pytest_addoption(parser):
    parser.addoption(
        "--profile",
        action="store_true",
        default=False,
        help="Profile performance tests and print cumulative hot functions.",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    if not item.config.getoption("--profile"):
        yield
        return

    profiler = cProfile.Profile()
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        item.config._nrg_profiles = getattr(item.config, "_nrg_profiles", [])
        item.config._nrg_profiles.append((item.nodeid, profiler))


def pytest_terminal_summary(terminalreporter):
    profiles = getattr(terminalreporter.config, "_nrg_profiles", [])
    if not profiles:
        return

    terminalreporter.section("NRG performance profile")
    for nodeid, profiler in profiles[:10]:
        stream = StringIO()
        stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
        stats.print_stats(12)
        terminalreporter.write_line(nodeid)
        terminalreporter.write(stream.getvalue())


def pytest_collection_modifyitems(items):
    for item in items:
        item_path = Path(str(item.fspath)).resolve()
        if THIS_DIR in item_path.parents or item_path.parent == THIS_DIR:
            item.add_marker(pytest.mark.load)
            item.add_marker(pytest.mark.slow)
