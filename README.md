# 389ds-log-analyser

This project provides a command-line tool to parse and analyze 389 Directory Server access logs. It can identify and report on completed connections, open connections, unindexed searches, and more.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/389ds-log-analyser.git
    cd 389ds-log-analyser
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the project in editable mode:**
    ```bash
    pip install -e '.[dev]'
    ```

## Usage

The primary command is `389ds-log-analyser`. It requires a log file to be specified with the `-f` or `--file` argument.

```bash
389ds-log-analyser -f <path_to_log_file> --query <query_mode>
```

### Filtering by Client IP

The `--filter-client-ip` argument allows you to filter the output to show connections only from one or more specific source IPs. This filter applies to all query modes as well as the default JSON output.

**Usage:**
```bash
# Filter for a single IP
389ds-log-analyser -f <log_file> --filter-client-ip 192.168.1.10

# Filter for multiple IPs
389ds-log-analyser -f <log_file> --query src_ip_table --filter-client-ip 192.168.1.10 192.168.1.11
```

### Query Modes

The `--query` argument allows you to generate summarized, human-readable reports instead of the full JSON output.


#### Show Completed Connections (`src_ip_table`)

This query displays a table of all connections that have a successful `BIND` and have been closed. The table includes the source IP, bind timestamp, and unbind timestamp.

**Usage:**
```bash
389ds-log-analyser -f <path_to_log_file> --query src_ip_table
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
389ds-log-analyser -f <path_to_log_file> --query open_connections
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
389ds-log-analyser -f <path_to_log_file> --query unique_clients
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

#### Show Unindexed Searches (`unindexed_searches`)

This query is essential for performance tuning. It identifies and lists all search operations (`SRCH`) that resulted in a `Partially Unindexed Filter` note, which can indicate missing database indexes.

**Usage:**
```bash
389ds-log-analyser -f <path_to_log_file> --query unindexed_searches
```

**Example Output:**
```
Timestamp                           Conn       Op         Base                           Filter
----------------------------------- ---------- ---------- ------------------------------ ----------------------------------------
2025-06-10T11:06:44.711859+02:00    105        1          dc=example,dc=com              (&(objectClass=ipHost)(ipHostNumber=10.31.50.48))
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

