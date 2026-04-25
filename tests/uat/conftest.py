import pytest
from pathlib import Path


THIS_DIR = Path(__file__).parent.resolve()


def pytest_collection_modifyitems(items):
    for item in items:
        item_path = Path(str(item.fspath)).resolve()
        if THIS_DIR in item_path.parents or item_path.parent == THIS_DIR:
            item.add_marker(pytest.mark.uat)
            item.add_marker(pytest.mark.slow)
