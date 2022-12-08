"""Test the 'znflow.utils' module."""
import pytest

from znflow import utils


class ConvertToString(utils.IterableHandler):
    """Convert any value to a string."""

    def default(self, value, **kwargs):
        """Update 'value'."""
        text = kwargs.pop("text", None)
        return str(value) + text if text else str(value)


@pytest.mark.parametrize(
    ("value", "result"),
    [
        (1, "1"),
        ([1], ["1"]),
        ([1, 2], ["1", "2"]),
        ((1, 2), ("1", "2")),
        ({1, 2}, {"1", "2"}),
        ({"a": 1, "b": 2}, {"a": "1", "b": "2"}),
        ([(1, {2, 3})], [("1", {"2", "3"})]),
    ],
)
def test_ConvertToString(value, result):
    """Test 'ConvertToString'."""
    assert ConvertToString().handle(value) == result
    assert ConvertToString()(value) == result


@pytest.mark.parametrize(
    ("value", "result"),
    [
        (1, "1."),
        ([1], ["1."]),
        ([1, 2], ["1.", "2."]),
        ((1, 2), ("1.", "2.")),
        ({1, 2}, {"1.", "2."}),
        ({"a": 1, "b": 2}, {"a": "1.", "b": "2."}),
        ([(1, {2, 3})], [("1.", {"2.", "3."})]),
    ],
)
def test_ConvertToString_arg(value, result):
    """Test 'ConvertToString' with 'text' argument."""
    assert ConvertToString().handle(value, text=".") == result
    assert ConvertToString()(value, text=".") == result
