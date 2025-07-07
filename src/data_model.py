# 389ds-log-analyser - A parser and query tool for 389 Directory Server access logs
# Copyright (C) 2024 Thomas Weiss <weiss@puzzle-itc.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pickle
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Type, ClassVar



# Assuming log_parser.py is in the same directory or accessible
from log_parser import parse_log_line

class LogDataModel:
    """Encapsulates the entire data model for easy persistence."""
    connections: Dict[int, 'Connection']

    def __init__(self, connections: Optional[Dict[int, 'Connection']] = None) -> None:
        self.connections = connections if connections is not None else {}

    def to_dict(self) -> Dict[int, Any]:
        """Converts the entire data model to a dictionary."""
        return {conn_num: conn.to_dict() for conn_num, conn in self.connections.items()}

    def save(self, file_path: str) -> None:
        """Saves the data model to a pickle file."""
        with open(file_path, 'wb') as f:
            pickle.dump(self, f)

    def save_json(self, file_path: str) -> None:
        """Saves the data model to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls: Type['LogDataModel'], file_path: str) -> 'LogDataModel':
        """Loads a data model from a file, detecting the format from the extension."""
        if str(file_path).endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            # The JSON data is just the connections dictionary
            return cls.from_dict(data)
        else:
            # Assume pickle format for any other extension
            with open(file_path, 'rb') as f:
                # For backward compatibility, we might load just the dictionary
                loaded_data = pickle.load(f)
                if isinstance(loaded_data, dict):
                    return cls(loaded_data)
            return loaded_data # It's a full LogDataModel object

    @classmethod
    def from_dict(cls: Type['LogDataModel'], data: Dict[str, Any]) -> 'LogDataModel':
        """Creates a LogDataModel from a dictionary (e.g., from JSON)."""
        connections = {int(k): Connection.from_dict(v) for k, v in data.items()}
        return cls(connections)

class Operation:
    """Represents a single operation within a connection."""
    op_num: int
    op_type: str
    timestamp: Optional[datetime]
    data: Dict[str, Any]
    extra_text: Optional[str]
    result: Optional[Any]

    def __init__(self, op_num: int, op_type: str, timestamp: Optional[datetime], data: Dict[str, Any], extra_text: Optional[str] = None) -> None:
        self.op_num = op_num
        self.op_type = op_type
        self.timestamp = timestamp
        self.data = data
        self.extra_text = extra_text
        self.result = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the operation to a dictionary for JSON serialization."""
        # The 'data' and 'result' fields are dictionaries that might contain
        # a datetime object from the parser. We need to convert it to a string.
        data_payload = self.data.copy()
        if 'timestamp' in data_payload and isinstance(data_payload.get('timestamp'), datetime):
            data_payload['timestamp'] = data_payload['timestamp'].isoformat()

        data_dict: Dict[str, Any] = {
            "op_num": self.op_num,
            "type": self.op_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "data": data_payload,
        }
        if self.extra_text:
            data_dict["extra_text"] = self.extra_text
        if self.result:
            if isinstance(self.result, dict):
                result_payload = self.result.copy()
                if 'timestamp' in result_payload and isinstance(result_payload.get('timestamp'), datetime):
                    result_payload['timestamp'] = result_payload['timestamp'].isoformat()
                data_dict["result"] = result_payload
            else:
                 data_dict["result"] = self.result
        return data_dict

    @classmethod
    def from_dict(cls: Type['Operation'], data: Dict[str, Any]) -> 'Operation':
        """Creates an Operation from a dictionary."""
        # Convert timestamp string back to datetime object
        timestamp = datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None
        op = cls(data['op_num'], data['type'], timestamp, data['data'], data.get('extra_text'))
        
        # Handle result, converting timestamp if present
        if 'result' in data and data['result']:
            if isinstance(data['result'], dict) and 'timestamp' in data['result']:
                data['result']['timestamp'] = datetime.fromisoformat(data['result']['timestamp'])
            op.result = data['result']
            
        return op

class Connection:
    """Represents a client connection and its operations."""
    conn_num: int
    bind_timestamp: Optional[datetime]
    unbind_timestamp: Optional[datetime]
    bind_dn: Optional[str]
    successful_bind: bool
    operations: Dict[int, Operation]
    source_ip: Optional[str]
    source_hostname: Optional[str]
    destination_ip: Optional[str]

    def __init__(self, conn_num: int) -> None:
        self.conn_num = conn_num
        self.bind_timestamp = None
        self.unbind_timestamp = None
        self.bind_dn = None
        self.successful_bind = False
        self.operations = {}
        self.source_ip = None
        self.source_hostname = None
        self.destination_ip = None

    def add_operation(self, op_num: Optional[int], op_type: str, timestamp: Optional[datetime], data: Dict[str, Any], extra_text: Optional[str]) -> None:
        """Adds or updates an operation in the connection."""
        # Handle connection info lines, which describe the connection itself.
        if op_type == "CONNECTION_INFO":
            self.source_ip = data.get('source_ip')
            self.destination_ip = data.get('destination_ip')
            return # This is not an operation, so we just update the connection and return.

        # A connection is closed when the parser identifies a 'Disconnect' operation.
        if op_type == "Disconnect":
            self.unbind_timestamp = timestamp
            # This message's only purpose for us is to mark the connection as closed.
            # We can return, as it doesn't need to be stored as a discrete operation.
            return

        # Only process operations that have an operation number from here on.
        if op_num is None:
            return

        if op_type == "RESULT":
            if op_num in self.operations:
                self.operations[op_num].result = data
                # Check if this is a result for a BIND operation
                if self.operations[op_num].op_type == "BIND" and isinstance(data, dict) and data.get('err') == 0:
                    self.successful_bind = True
                    self.bind_timestamp = self.operations[op_num].timestamp
                    # The DN is often in the RESULT of the BIND, not the BIND itself
                    if isinstance(data, dict) and 'dn' in data:
                        self.bind_dn = data.get('dn')
                    elif isinstance(self.operations[op_num].data, dict):
                        self.bind_dn = self.operations[op_num].data.get('dn')
        else:
            # Log the BIND, UNBIND, SRCH, etc. operations.
            if op_num not in self.operations:
                self.operations[op_num] = Operation(op_num, op_type, timestamp, data, extra_text)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the connection to a dictionary for JSON serialization."""
        return {
            "connection_num": self.conn_num,
            "source_ip": self.source_ip,
            "source_hostname": self.source_hostname,
            "destination_ip": self.destination_ip,
            "bind_dn": self.bind_dn,
            "bind_timestamp": self.bind_timestamp.isoformat() if self.bind_timestamp else None,
            "unbind_timestamp": self.unbind_timestamp.isoformat() if self.unbind_timestamp else None,
            "operations": sorted([op.to_dict() for op in self.operations.values()], key=lambda x: x.get('op_num', 0))
        }

    @classmethod
    def from_dict(cls: Type['Connection'], data: Dict[str, Any]) -> 'Connection':
        """Creates a Connection from a dictionary."""
        conn = cls(data['connection_num'])
        conn.source_ip = data.get('source_ip')
        conn.source_hostname = data.get('source_hostname')
        conn.destination_ip = data.get('destination_ip')
        conn.bind_dn = data.get('bind_dn')
        conn.bind_timestamp = datetime.fromisoformat(data['bind_timestamp']) if data.get('bind_timestamp') else None
        conn.unbind_timestamp = datetime.fromisoformat(data['unbind_timestamp']) if data.get('unbind_timestamp') else None
        
        # Recreate operations from the dictionary list
        conn.operations = {op_data['op_num']: Operation.from_dict(op_data) for op_data in data['operations']}
        
        # Recalculate successful_bind based on loaded data
        for op in conn.operations.values():
            if op.op_type == "BIND" and isinstance(op.result, dict) and op.result.get('err') == 0:
                conn.successful_bind = True
                break
        
        return conn

def build_data_model(log_file_path: str, debug: bool = False) -> LogDataModel:
    """Parses a log file and builds a structured data model of connections."""
    connections: Dict[int, Connection] = {}

    with open(log_file_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                parsed = parse_log_line(line.strip())
            except Exception as e:
                if debug:
                    print(f"Failed to parse line: {line.strip()}\n{e}")
                continue

            if not parsed or 'conn' not in parsed:
                continue

            conn_id = parsed.get('conn')
            op_num = parsed.get('op')
            op_type = parsed.get('type')
            timestamp = parsed.get('timestamp')
            extra_text = parsed.get('extra_text') # This might be None

            if conn_id not in connections:
                connections[conn_id] = Connection(conn_id)

            # Pass the entire parsed dictionary as the 'data' payload
            connections[conn_id].add_operation(op_num, op_type, timestamp, parsed, extra_text)

    return LogDataModel(connections)


