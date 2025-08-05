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
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Type, ClassVar

# Import custom exceptions
try:
    from .exceptions import (
        LogAnalyserError, FileOperationError, LogFileNotFoundError, 
        LogFilePermissionError, DataModelFileError, LogParsingError,
        DataModelError, EmptyLogFileError, CorruptedDataModelError
    )
except ImportError:
    from exceptions import (
        LogAnalyserError, FileOperationError, LogFileNotFoundError, 
        LogFilePermissionError, DataModelFileError, LogParsingError,
        DataModelError, EmptyLogFileError, CorruptedDataModelError
    )

# Assuming log_parser.py is in the same directory or accessible
try:
    from .log_parser import parse_log_line, LogParsingError as ParserError
except ImportError:
    from log_parser import parse_log_line, LogParsingError as ParserError

# Set up logging
logger = logging.getLogger(__name__)

class LogDataModel:
    """Encapsulates the entire data model for easy persistence."""
    connections: Dict[int, 'Connection']

    def __init__(self, connections: Optional[Dict[int, 'Connection']] = None) -> None:
        self.connections = connections if connections is not None else {}

    def to_dict(self) -> Dict[int, Any]:
        """Converts the entire data model to a dictionary."""
        try:
            return {conn_num: conn.to_dict() for conn_num, conn in self.connections.items()}
        except Exception as e:
            raise DataModelError(
                "Failed to convert data model to dictionary",
                operation="to_dict",
                details="Error occurred while serializing connection data",
                cause=e
            )

    def save(self, file_path: str) -> None:
        """Saves the data model to a pickle file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                pickle.dump(self, f)
            
            logger.info(f"Data model saved to {file_path}")
            
        except PermissionError as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="save",
                details="Permission denied - check write permissions for the directory",
                cause=e
            )
        except OSError as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="save",
                details="File system error occurred",
                cause=e
            )
        except Exception as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="save",
                details="Unexpected error during pickle serialization",
                cause=e
            )

    def save_json(self, file_path: str) -> None:
        """Saves the data model to a JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            data_dict = self.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data model saved as JSON to {file_path}")
            
        except PermissionError as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="save_json",
                details="Permission denied - check write permissions for the directory",
                cause=e
            )
        except OSError as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="save_json",
                details="File system error occurred",
                cause=e
            )
        except (TypeError, ValueError) as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="save_json",
                details="JSON serialization failed - data may contain non-serializable objects",
                cause=e
            )
        except Exception as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="save_json",
                details="Unexpected error during JSON serialization",
                cause=e
            )

    @classmethod
    def load(cls: Type['LogDataModel'], file_path: str) -> 'LogDataModel':
        """Loads a data model from a file, detecting the format from the extension."""
        if not os.path.exists(file_path):
            raise LogFileNotFoundError(file_path)
        
        if not os.access(file_path, os.R_OK):
            raise LogFilePermissionError(file_path)
        
        try:
            if str(file_path).endswith('.json'):
                return cls._load_json(file_path)
            else:
                return cls._load_pickle(file_path)
                
        except (LogFileNotFoundError, LogFilePermissionError):
            # Re-raise these specific exceptions
            raise
        except Exception as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="load",
                details="Failed to determine file format or load data",
                cause=e
            )

    @classmethod
    def _load_json(cls: Type['LogDataModel'], file_path: str) -> 'LogDataModel':
        """Loads a data model from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                raise CorruptedDataModelError(file_path, "JSON")
            
            logger.info(f"Data model loaded from JSON file: {file_path}")
            return cls.from_dict(data)
            
        except json.JSONDecodeError as e:
            raise CorruptedDataModelError(file_path, "JSON", cause=e)
        except (KeyError, ValueError, TypeError) as e:
            raise CorruptedDataModelError(
                file_path, "JSON", 
                cause=DataModelError("Invalid JSON structure for data model", cause=e)
            )
        except Exception as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="load_json",
                details="Unexpected error during JSON deserialization",
                cause=e
            )

    @classmethod
    def _load_pickle(cls: Type['LogDataModel'], file_path: str) -> 'LogDataModel':
        """Loads a data model from a pickle file."""
        try:
            with open(file_path, 'rb') as f:
                loaded_data = pickle.load(f)
            
            # Handle backward compatibility
            if isinstance(loaded_data, dict):
                logger.info(f"Loading legacy data model format from: {file_path}")
                return cls(loaded_data)
            elif isinstance(loaded_data, cls):
                logger.info(f"Data model loaded from pickle file: {file_path}")
                return loaded_data
            else:
                raise CorruptedDataModelError(file_path, "pickle")
                
        except pickle.UnpicklingError as e:
            raise CorruptedDataModelError(file_path, "pickle", cause=e)
        except (AttributeError, ImportError) as e:
            raise CorruptedDataModelError(
                file_path, "pickle",
                cause=DataModelError("Pickle file contains incompatible class definitions", cause=e)
            )
        except Exception as e:
            raise DataModelFileError(
                file_path=file_path,
                operation="load_pickle",
                details="Unexpected error during pickle deserialization",
                cause=e
            )

    @classmethod
    def from_dict(cls: Type['LogDataModel'], data: Dict[str, Any]) -> 'LogDataModel':
        """Creates a LogDataModel from a dictionary (e.g., from JSON)."""
        try:
            connections = {}
            for k, v in data.items():
                try:
                    conn_id = int(k)
                    connections[conn_id] = Connection.from_dict(v)
                except (ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid connection ID '{k}': {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Failed to load connection {k}: {e}")
                    continue
            
            return cls(connections)
            
        except Exception as e:
            raise DataModelError(
                "Failed to create data model from dictionary",
                operation="from_dict",
                details="Error occurred while deserializing connection data",
                cause=e
            )

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
        try:
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
        except Exception as e:
            raise DataModelError(
                f"Failed to convert operation {self.op_num} to dictionary",
                operation="operation_to_dict",
                cause=e
            )

    @classmethod
    def from_dict(cls: Type['Operation'], data: Dict[str, Any]) -> 'Operation':
        """Creates an Operation from a dictionary."""
        try:
            # Convert timestamp string back to datetime object
            timestamp = None
            if data.get('timestamp'):
                try:
                    timestamp = datetime.fromisoformat(data['timestamp'])
                except ValueError as e:
                    logger.warning(f"Invalid timestamp format in operation data: {data.get('timestamp')}")
                    
            op = cls(data['op_num'], data['type'], timestamp, data['data'], data.get('extra_text'))
            
            # Handle result, converting timestamp if present
            if 'result' in data and data['result']:
                if isinstance(data['result'], dict) and 'timestamp' in data['result']:
                    try:
                        data['result']['timestamp'] = datetime.fromisoformat(data['result']['timestamp'])
                    except ValueError as e:
                        logger.warning(f"Invalid timestamp format in result data: {data['result']['timestamp']}")
                op.result = data['result']
                
            return op
            
        except KeyError as e:
            raise DataModelError(
                f"Missing required field in operation data: {e}",
                operation="operation_from_dict",
                cause=e
            )
        except Exception as e:
            raise DataModelError(
                "Failed to create operation from dictionary",
                operation="operation_from_dict",
                cause=e
            )

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
        try:
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
                    logger.warning(f"Received RESULT for unknown operation {op_num} in connection {self.conn_num}")
            else:
                # Log the BIND, UNBIND, SRCH, etc. operations.
                if op_num not in self.operations:
                    self.operations[op_num] = Operation(op_num, op_type, timestamp, data, extra_text)
                else:
                    logger.warning(f"Duplicate operation {op_num} in connection {self.conn_num}")
                    
        except Exception as e:
            logger.error(f"Error adding operation to connection {self.conn_num}: {e}")
            # Don't raise here to allow parsing to continue

    def to_dict(self) -> Dict[str, Any]:
        """Converts the connection to a dictionary for JSON serialization."""
        try:
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
        except Exception as e:
            raise DataModelError(
                f"Failed to convert connection {self.conn_num} to dictionary",
                operation="connection_to_dict",
                cause=e
            )

    @classmethod
    def from_dict(cls: Type['Connection'], data: Dict[str, Any]) -> 'Connection':
        """Creates a Connection from a dictionary."""
        try:
            conn = cls(data['connection_num'])
            conn.source_ip = data.get('source_ip')
            conn.source_hostname = data.get('source_hostname')
            conn.destination_ip = data.get('destination_ip')
            conn.bind_dn = data.get('bind_dn')
            
            # Handle timestamps
            if data.get('bind_timestamp'):
                try:
                    conn.bind_timestamp = datetime.fromisoformat(data['bind_timestamp'])
                except ValueError as e:
                    logger.warning(f"Invalid bind_timestamp format: {data['bind_timestamp']}")
                    
            if data.get('unbind_timestamp'):
                try:
                    conn.unbind_timestamp = datetime.fromisoformat(data['unbind_timestamp'])
                except ValueError as e:
                    logger.warning(f"Invalid unbind_timestamp format: {data['unbind_timestamp']}")
            
            # Recreate operations from the dictionary list
            conn.operations = {}
            for op_data in data.get('operations', []):
                try:
                    op = Operation.from_dict(op_data)
                    conn.operations[op.op_num] = op
                except Exception as e:
                    logger.warning(f"Failed to load operation {op_data.get('op_num', 'unknown')} for connection {conn.conn_num}: {e}")
                    continue
            
            # Recalculate successful_bind based on loaded data
            for op in conn.operations.values():
                if op.op_type == "BIND" and isinstance(op.result, dict) and op.result.get('err') == 0:
                    conn.successful_bind = True
                    break
            
            return conn
            
        except KeyError as e:
            raise DataModelError(
                f"Missing required field in connection data: {e}",
                operation="connection_from_dict",
                cause=e
            )
        except Exception as e:
            raise DataModelError(
                "Failed to create connection from dictionary",
                operation="connection_from_dict",
                cause=e
            )

def build_data_model(log_file_path: str, debug: bool = False) -> LogDataModel:
    """Parses a log file and builds a structured data model of connections."""
    if not os.path.exists(log_file_path):
        raise LogFileNotFoundError(log_file_path)
    
    if not os.access(log_file_path, os.R_OK):
        raise LogFilePermissionError(log_file_path)
    
    connections: Dict[int, Connection] = {}
    line_count = 0
    parsed_lines = 0
    error_count = 0
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                line_count += 1
                
                if not line.strip():
                    continue
                
                try:
                    parsed = parse_log_line(line.strip())
                    if parsed:
                        parsed_lines += 1
                        
                        if 'conn' not in parsed:
                            if debug:
                                logger.debug(f"Line {line_number}: No connection ID found")
                            continue

                        conn_id = parsed.get('conn')
                        op_num = parsed.get('op')
                        op_type = parsed.get('type')
                        timestamp = parsed.get('timestamp')
                        extra_text = parsed.get('extra_text')

                        if conn_id not in connections:
                            connections[conn_id] = Connection(conn_id)

                        # Pass the entire parsed dictionary as the 'data' payload
                        connections[conn_id].add_operation(op_num, op_type, timestamp, parsed, extra_text)
                    else:
                        if debug:
                            logger.debug(f"Line {line_number}: Failed to parse - {line.strip()[:100]}")
                        
                except Exception as e:
                    error_count += 1
                    if debug:
                        logger.error(f"Line {line_number}: Parse error - {e}")
                        logger.debug(f"Line content: {line.strip()[:200]}")
                    continue
    
    except UnicodeDecodeError as e:
        raise LogParsingError(
            f"File encoding error in {log_file_path}",
            details="File may not be UTF-8 encoded or may be corrupted",
            cause=e
        )
    except OSError as e:
        raise FileOperationError(
            f"Error reading log file: {log_file_path}",
            file_path=log_file_path,
            operation="read",
            cause=e
        )
    
    # Check if we got any useful data
    if not connections:
        raise EmptyLogFileError(log_file_path)
    
    # Log statistics
    logger.info(f"Parsed {parsed_lines} lines out of {line_count} total lines")
    if error_count > 0:
        logger.warning(f"Encountered {error_count} parsing errors")
    
    logger.info(f"Built data model with {len(connections)} connections")
    
    return LogDataModel(connections)


