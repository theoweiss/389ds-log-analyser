This project provides tools to parse and analyze 389-ds access logs.

## `log_parser.py`

This script parses raw 389-ds access logs and outputs a stream of JSON objects, one for each log line.

### Usage

```bash
python src/log_parser.py -f <path_to_log_file>
```

## `data_model.py`

This script processes the logs to build a structured data model of connections. It identifies connections that are successfully established with a `BIND` operation and terminated with an `UNBIND`, and it lists all associated operations.

### Usage

By default, the script outputs a JSON array of all successfully completed connections.

```bash
python src/data_model.py -f <path_to_log_file>
```

### Query Modes

The `--query` argument allows you to generate summarized, human-readable reports instead of the full JSON output.


#### Show Completed Connections (`src_ip_table`)

This query displays a table of all connections that have a successful `BIND` and have been closed. The table includes the source IP, bind timestamp, and unbind timestamp.

**Usage:**
```bash
python src/data_model.py -f <path_to_log_file> --query src_ip_table
```

**Example Output:**
```
Source IP            Bind Timestamp                      Unbind Timestamp
-------------------- ----------------------------------- -----------------------------------
192.168.1.10         2025-06-10T21:18:06.100000+00:00    2025-06-10T21:18:07.200000+00:00
... 
```

#### Show Open Connections (`open_connections`)

This query displays a table of all connections that have a successful `BIND` but have not yet been closed. This is useful for monitoring currently active sessions.

**Usage:**
```bash
python src/data_model.py -f <path_to_log_file> --query open_connections
```

**Example Output:**
```
Source IP            Bind DN                                     Bind Timestamp
-------------------- -------------------------------------------------- -----------------------------------
192.168.1.12         uid=another,ou=people,dc=example,dc=com     2025-06-10T21:18:12.100000+00:00
... 
```

#### Show Unique Client IPs (`unique_clients`)

This query scans all connections and prints a unique, sorted list of all source IP addresses that have connected to the server.

**Usage:**
```bash
python src/data_model.py -f <path_to_log_file> --query unique_clients
```

**Example Output:**
```
Unique Client IPs
-----------------
192.168.1.10
192.168.1.11
192.168.1.12
192.168.1.13
local
```

### Default JSON Output Structure

The script outputs a JSON array of connection objects with the following structure:

```json
[
  {
    "connection_num": 123,
    "bind_dn": "cn=Directory Manager",
    "bind_timestamp": "2025-06-10T12:00:00+02:00",
    "unbind_timestamp": "2025-06-10T12:01:00+02:00",
    "operations": [
      {
        "op_num": 0,
        "type": "BIND",
        "timestamp": "2025-06-10T12:00:00+02:00",
        "data": {
          "dn": "cn=Directory Manager",
          "method": 128,
          "version": 3
        },
        "result": {
          "err": 0,
          "tag": 97,
          "nentries": 0
        }
      },
      {
        "op_num": 1,
        "type": "SRCH",
        "timestamp": "2025-06-10T12:00:30+02:00",
        "data": {
          "base": "ou=People,dc=example,dc=com",
          "scope": 2,
          "filter": "(uid=testuser)",
          "attrs": "ALL"
        },
        "result": {
          "err": 0,
          "tag": 101,
          "nentries": 1
        }
      },
      {
        "op_num": 2,
        "type": "UNBIND",
        "timestamp": "2025-06-10T12:01:00+02:00",
        "data": {},
        "result": null
      }
    ]
  }
]
```

