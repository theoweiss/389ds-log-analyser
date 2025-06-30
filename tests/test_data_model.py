import pytest
from datetime import datetime, timezone
import os
from data_model import LogDataModel, build_data_model

@pytest.fixture
def model():
    """Builds a data model from the test log file."""
    log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.log'))
    return build_data_model(log_file)

def test_build_data_model_connections(model):
    """Tests that the connection is created correctly."""
    assert len(model.connections) == 1
    conn = model.connections[100]
    assert conn.conn_num == 100
    assert conn.bind_dn == "uid=test,ou=people,dc=example,dc=com"
    assert conn.bind_timestamp == datetime(2025, 6, 10, 21, 18, 6, 100000, tzinfo=timezone.utc)
    assert conn.unbind_timestamp == datetime(2025, 6, 10, 21, 18, 7, 300000, tzinfo=timezone.utc)

def test_build_data_model_operations(model):
    """Tests that operations are added to the connection correctly."""
    conn = model.connections[100]
    assert len(conn.operations) == 2
    assert conn.operations[0].op_type == "BIND"
    assert conn.operations[1].op_type == "SRCH"
    assert conn.operations[1].result['err'] == 0

def test_save_and_load_data_model(model, tmp_path):
    """Tests that the data model can be saved and loaded correctly."""
    file_path = tmp_path / "datamodel.pkl"
    model.save(file_path)

    assert os.path.exists(file_path)

    loaded_model = LogDataModel.load(file_path)

    assert len(loaded_model.connections) == len(model.connections)
    original_conn = model.connections[100]
    loaded_conn = loaded_model.connections[100]

    assert loaded_conn.conn_num == original_conn.conn_num
    assert loaded_conn.bind_dn == original_conn.bind_dn
    assert loaded_conn.bind_timestamp == original_conn.bind_timestamp
    assert loaded_conn.unbind_timestamp == original_conn.unbind_timestamp
    assert len(loaded_conn.operations) == len(original_conn.operations)

def test_save_and_load_json(model, tmp_path):
    """Tests that the data model can be saved and loaded correctly in JSON format."""
    file_path = tmp_path / "datamodel.json"
    model.save_json(file_path)

    assert os.path.exists(file_path)

    loaded_model = LogDataModel.load(file_path)

    assert len(loaded_model.connections) == len(model.connections)
    original_conn = model.connections[100]
    loaded_conn = loaded_model.connections[100]

    assert loaded_conn.conn_num == original_conn.conn_num
    assert loaded_conn.bind_dn == original_conn.bind_dn
    assert loaded_conn.bind_timestamp == original_conn.bind_timestamp
    assert loaded_conn.unbind_timestamp == original_conn.unbind_timestamp
    assert len(loaded_conn.operations) == len(original_conn.operations)

