"""Test 'znflow.graph'."""
import pytest

import znflow.base


def test_nested_dag():
    """Test nested DAGs."""
    with znflow.DiGraph():
        with pytest.raises(ValueError):
            with znflow.DiGraph():
                pass


def test_changed_dag():
    """Test changed DAGs."""
    with pytest.raises(ValueError):
        with znflow.DiGraph():
            znflow.base.NodeBaseMixin._graph_ = znflow.DiGraph()
    znflow.base.NodeBaseMixin._graph_ = None  # reset after test
