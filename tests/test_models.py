import pytest

from docflow.models import get_model


def test_unknown_model_raises():
    with pytest.raises(ValueError):
        get_model("nope")


def test_known_models_resolve():
    """The registry wires each name to its class. Cls.from_name is lazy, so the Modal
    case needs no deployed app or auth; 'dots' needs a server URL, so only check 'modal'
    and 'mock' here (the offline ones)."""
    assert get_model("mock").__class__.__name__ == "MockLayoutModel"
    assert get_model("modal").__class__.__name__ == "ModalDotsModel"
