import pytest
from datetime import datetime, timezone
import sys
import os

# Add src directory to path to import data_model
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from data_model import build_data_model

@pytest.fixture
def model():
    """Builds a data model from the test log file."""
    log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.log'))
    return build_data_model(log_file)

def test_build_data_model_connections(model):
    """Tests that the connection is created correctly."""
    assert len(model) == 1
    conn = model[100]
    assert conn.conn_num == 100
    assert conn.bind_dn == "uid=test,ou=people,dc=example,dc=com"
    assert conn.bind_timestamp == datetime(2025, 6, 10, 21, 18, 6, 100000, tzinfo=timezone.utc)
    assert conn.unbind_timestamp == datetime(2025, 6, 10, 21, 18, 7, 300000, tzinfo=timezone.utc)

def test_build_data_model_operations(model):
    """Tests that operations are added to the connection correctly."""
    conn = model[100]
    assert len(conn.operations) == 2
    assert conn.operations[0].op_type == "BIND"
    assert conn.operations[1].op_type == "SRCH"
    assert conn.operations[1].result['err'] == 0
