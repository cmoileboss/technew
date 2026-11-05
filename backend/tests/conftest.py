import pytest

from app import classifier


@pytest.fixture(autouse=True)
def no_real_classifier(monkeypatch):
    """Never load the real embedding model in tests; individual tests inject a fake classifier."""
    monkeypatch.setattr(classifier, "get_classifier", lambda: None)
