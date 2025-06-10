from datetime import datetime



# Assuming log_parser.py is in the same directory or accessible
from log_parser import parse_log_line

class Operation:
    """Represents a single operation within a connection."""
    def __init__(self, op_num, op_type, timestamp, data, extra_text=None):
        self.op_num = op_num
        self.op_type = op_type
        self.timestamp = timestamp
        self.data = data
        self.extra_text = extra_text
        self.result = None

    def to_dict(self):
        """Converts the operation to a dictionary for JSON serialization."""
        # The 'data' and 'result' fields are dictionaries that might contain
        # a datetime object from the parser. We need to convert it to a string.
        data_payload = self.data.copy()
        if 'timestamp' in data_payload and isinstance(data_payload.get('timestamp'), datetime):
            data_payload['timestamp'] = data_payload['timestamp'].isoformat()

        data_dict = {
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

class Connection:
    """Represents a client connection and its operations."""
    def __init__(self, conn_num):
        self.conn_num = conn_num
        self.bind_timestamp = None
        self.unbind_timestamp = None
        self.bind_dn = None
        self.successful_bind = False
        self.operations = {}
        self.source_ip = None
        self.destination_ip = None

    def add_operation(self, op_num, op_type, timestamp, data, extra_text):
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


    def to_dict(self):
        """Converts the connection to a dictionary for JSON serialization."""
        return {
            "connection_num": self.conn_num,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "bind_dn": self.bind_dn,
            "bind_timestamp": self.bind_timestamp.isoformat() if self.bind_timestamp else None,
            "unbind_timestamp": self.unbind_timestamp.isoformat() if self.unbind_timestamp else None,
            "operations": sorted([op.to_dict() for op in self.operations.values()], key=lambda x: x.get('op_num', 0))
        }

def build_data_model(log_file_path, debug=False):
    """Parses a log file and builds a structured data model of connections."""


    connections = {}

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

    return connections


