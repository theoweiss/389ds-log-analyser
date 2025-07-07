# 389ds-log-analyser

![License](https://img.shields.io/badge/license-GPL%20v3-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
[![Tests](https://github.com/theoweiss/389ds-log-analyser/actions/workflows/ci.yml/badge.svg)](https://github.com/theoweiss/389ds-log-analyser/actions/workflows/ci.yml)
[![Type Hints](https://img.shields.io/badge/typing-typed-green.svg)](https://mypy-lang.org/)

A powerful command-line tool for parsing and analyzing 389 Directory Server (formerly Red Hat Directory Server) access logs. This tool helps system administrators and developers monitor LDAP server performance, identify issues, and optimize directory server configurations.

## 🚀 Features

- **Multiple Analysis Commands**: Analyze completed connections, open connections, unique clients, unindexed searches, and detailed operation traces
- **Performance Optimization**: Identify unindexed searches that may impact server performance
- **Flexible Output**: Support for both human-readable tables and JSON export
- **Data Persistence**: Save parsed data models for faster subsequent analysis of large log files
- **Hostname Resolution**: Resolve IP addresses to hostnames with caching for better readability
- **Advanced Filtering**: Filter results by client IP addresses or bind DNs
- **Comprehensive CLI**: Tab completion support and multiple entry points for convenience
- **Type Safety**: Fully type-annotated codebase for better development experience

## 📋 Table of Contents

- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Commands](#-commands)
- [Advanced Features](#-advanced-features)
- [Examples](#-examples)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 💾 Installation

### From GitHub (Recommended)

```bash
pip install git+https://github.com/theoweiss/389ds-log-analyser.git
```

### Development Installation

```bash
git clone https://github.com/theoweiss/389ds-log-analyser.git
cd 389ds-log-analyser
pip install -e .
```

### Offline Installation

For environments without internet access:

1. **On a machine with internet access:**
   ```bash
   git clone https://github.com/theoweiss/389ds-log-analyser.git
   cd 389ds-log-analyser
   pip download -r requirements.txt -d dependencies/
   ```

2. **Transfer the entire directory to the offline machine**

3. **On the offline machine:**
   ```bash
   cd 389ds-log-analyser
   pip install --no-index --find-links dependencies/ .
   ```

## 🚀 Quick Start

```bash
# Analyze completed connections
389ds-log-analyser src-ip-table -f /var/log/dirsrv/slapd-instance/access

# Find performance issues
389ds-log-analyser unindexed-searches -f /var/log/dirsrv/slapd-instance/access

# Monitor active sessions
389ds-log-analyser open-connections -f /var/log/dirsrv/slapd-instance/access

# Get detailed operation trace for debugging
389ds-log-analyser connection-details -f /var/log/dirsrv/slapd-instance/access --conn-id 12345
```

## 💻 Usage

### Basic Syntax

```bash
389ds-log-analyser <command> -f <log_file> [options]
```

### Global Options

| Option | Description |
|--------|-------------|
| `-f, --file` | Path to the 389ds access log file |
| `-l, --load-datamodel` | Load a previously saved data model (mutually exclusive with `-f`) |
| `-p, --save-pickle` | Save parsed data model as pickle file for faster subsequent analysis |
| `-j, --save-json` | Save parsed data model as JSON file for inspection or integration |
| `--resolve-hostnames` | Resolve IP addresses to hostnames (may slow initial processing) |
| `--filter-client-ip` | Filter results to specific client IP address(es) |
| `--debug` | Enable debug output for parsing errors |
| `--version` | Show version information |

### Standalone Commands

For convenience, each command is available as a standalone script:

```bash
389ds-src-ip-table -f <log_file>
389ds-open-connections -f <log_file>
389ds-unique-clients -f <log_file>
389ds-unindexed-searches -f <log_file>
389ds-connection-details -f <log_file>
```

### Command Completion

Enable tab completion for better CLI experience:

```bash
# Temporary activation
eval "$(register-python-argcomplete 389ds-log-analyser)"

# Permanent activation (add to ~/.bashrc or ~/.zshrc)
echo 'eval "$(register-python-argcomplete 389ds-log-analyser)"' >> ~/.bashrc
```

## 🛠️ Commands

### `src-ip-table` - Completed Connections

Shows all connections that successfully bound and were properly closed.

```bash
389ds-log-analyser src-ip-table -f access.log
```

**Output:**
```
Source IP/Hostname                       Bind Timestamp                      Unbind Timestamp                   
---------------------------------------- ----------------------------------- -----------------------------------
192.168.1.10                             2025-06-10T21:18:06.100000+00:00    2025-06-10T21:18:07.200000+00:00
client-server.example.com                2025-06-10T21:18:08.100000+00:00    2025-06-10T21:18:11+00:00
```

### `open-connections` - Active Sessions

Displays currently active (not yet closed) connections.

```bash
389ds-log-analyser open-connections -f access.log
```

**Options:**
- `--filter-bind-dn`: Filter by specific bind DN(s)

**Output:**
```
Source IP/Hostname                       Bind DN                                           Bind Timestamp                     
---------------------------------------- ------------------------------------------------- -----------------------------------
192.168.1.12                             uid=serviceaccount,ou=people,dc=example,dc=com    2025-06-10T21:18:12.100000+00:00

Summary of Open Connections by Bind DN:
Bind DN                                                                Count
---------------------------------------------------------------------- -----
uid=serviceaccount,ou=people,dc=example,dc=com                         1
cn=Directory Manager                                                    2
```

### `unique-clients` - Client Inventory

Lists all unique client IP addresses that have connected.

```bash
389ds-log-analyser unique-clients -f access.log --resolve-hostnames
```

**Output:**
```
Unique Client Hostnames
-----------------------
app-server-01.example.com
app-server-02.example.com
monitoring.example.com
local

Total unique clients: 4
```

### `unindexed-searches` - Performance Analysis

**Critical for performance tuning!** Identifies searches that may benefit from additional database indexes.

```bash
389ds-log-analyser unindexed-searches -f access.log
```

**Output:**
```
Timestamp                           Conn       Op         Base                           Filter
----------------------------------- ---------- ---------- ------------------------------ ----------------------------------------
2025-06-10T11:06:44.711859+02:00    105        1          dc=example,dc=com              (&(objectClass=ipHost)(ipHostNumber=10.31.50.48))
2025-06-10T11:07:15.234567+02:00    106        3          ou=people,dc=example,dc=com    (&(department=Engineering)(status=active))
```

### `connection-details` - Detailed Operation Trace

Provides comprehensive debugging information for connection troubleshooting.

```bash
# All connections
389ds-log-analyser connection-details -f access.log

# Specific connection
389ds-log-analyser connection-details -f access.log --conn-id 12345
```

**Output:**
```
--- Connection: 12345 | Source: app-server-01.example.com | Bind DN: uid=appuser,ou=people,dc=example,dc=com ---
  Op: 0     | Type: BIND     | Timestamp: 2025-06-10 12:00:00
  Op: 1     | Type: SRCH     | Timestamp: 2025-06-10 12:00:01 | Base: ou=people,dc=example,dc=com | Filter: (uid=testuser) | Attrs: cn uid mail
  Op: 2     | Type: SRCH     | Timestamp: 2025-06-10 12:00:02 | Base: ou=groups,dc=example,dc=com | Filter: (member=uid=testuser,ou=people,dc=example,dc=com) | Attrs: cn
```

## 🔧 Advanced Features

### Data Model Persistence

For large log files, save parsed data for faster subsequent analysis:

```bash
# Save as pickle (fastest)
389ds-log-analyser src-ip-table -f large-access.log -p datamodel.pkl

# Save as JSON (human-readable)
389ds-log-analyser src-ip-table -f large-access.log -j datamodel.json

# Load saved data model
389ds-log-analyser open-connections -l datamodel.pkl
```

### Hostname Resolution with Caching

```bash
# Resolve hostnames (slower initial run, but results are cached)
389ds-log-analyser src-ip-table -f access.log --resolve-hostnames -p cached-model.pkl

# Subsequent runs using cached model are fast
389ds-log-analyser open-connections -l cached-model.pkl
```

### Advanced Filtering

```bash
# Filter by single IP
389ds-log-analyser src-ip-table -f access.log --filter-client-ip 192.168.1.10

# Filter by multiple IPs
389ds-log-analyser src-ip-table -f access.log --filter-client-ip 192.168.1.10 192.168.1.11

# Filter open connections by bind DN
389ds-log-analyser open-connections -f access.log --filter-bind-dn "cn=Directory Manager"
```

## 📚 Examples

### Daily Performance Report

```bash
#!/bin/bash
LOG_FILE="/var/log/dirsrv/slapd-instance/access"
REPORT_DATE=$(date +%Y-%m-%d)

echo "=== 389ds Performance Report - $REPORT_DATE ===" > report.txt
echo "" >> report.txt

echo "Unindexed Searches:" >> report.txt
389ds-log-analyser unindexed-searches -f "$LOG_FILE" >> report.txt
echo "" >> report.txt

echo "Currently Open Connections:" >> report.txt
389ds-log-analyser open-connections -f "$LOG_FILE" --resolve-hostnames >> report.txt
echo "" >> report.txt

echo "Unique Clients Today:" >> report.txt
389ds-log-analyser unique-clients -f "$LOG_FILE" --resolve-hostnames >> report.txt
```

### Investigating Connection Issues

```bash
# 1. Find problematic client
389ds-log-analyser unique-clients -f access.log

# 2. Filter connections from specific client
389ds-log-analyser src-ip-table -f access.log --filter-client-ip 192.168.1.100

# 3. Get detailed trace for debugging
389ds-log-analyser connection-details -f access.log --filter-client-ip 192.168.1.100
```

### Performance Optimization Workflow

```bash
# 1. Identify unindexed searches
389ds-log-analyser unindexed-searches -f access.log > unindexed.txt

# 2. Analyze patterns in the filters
cat unindexed.txt | awk '{print $NF}' | sort | uniq -c | sort -nr

# 3. Create appropriate indexes based on common filter patterns
# 4. Re-run analysis after index creation to verify improvement
```

## 📖 API Documentation

### Data Model Classes

The tool provides a programmatic API for custom analysis:

```python
from data_model import LogDataModel, build_data_model

# Parse log file
data_model = build_data_model("/path/to/access.log", debug=True)

# Access connections
for conn_id, connection in data_model.connections.items():
    print(f"Connection {conn_id}: {connection.source_ip} -> {connection.bind_dn}")
    
    # Access operations
    for op_id, operation in connection.operations.items():
        print(f"  Operation {op_id}: {operation.op_type} at {operation.timestamp}")

# Save/load data models
data_model.save("model.pkl")
data_model.save_json("model.json")
loaded_model = LogDataModel.load("model.pkl")
```

### Log Parser Functions

```python
from log_parser import parse_log_line, parse_timestamp

# Parse individual log lines
line = '[10/Jun/2025:21:18:06.100000Z] conn=100 op=0 BIND dn="uid=test,ou=people,dc=example,dc=com"'
parsed = parse_log_line(line)
print(parsed)  # {'type': 'BIND', 'conn': 100, 'op': 0, 'dn': 'uid=test,ou=people,dc=example,dc=com', ...}

# Parse timestamps
timestamp = parse_timestamp("10/Jun/2025:21:18:06.100000Z")
print(timestamp)  # datetime object with timezone
```

## 🐛 Troubleshooting

### Common Issues

**Problem: No output from commands**
```bash
# Check if log file exists and is readable
ls -la /path/to/access.log

# Enable debug mode to see parsing errors
389ds-log-analyser src-ip-table -f access.log --debug
```

**Problem: "Command not found" after installation**
```bash
# Check if installation location is in PATH
pip show 389ds-log-analyser

# Try running with python -m
python -m cli src-ip-table -f access.log
```

**Problem: Slow performance with large files**
```bash
# Use data model persistence for large files
389ds-log-analyser src-ip-table -f large.log -p model.pkl
# Subsequent runs:
389ds-log-analyser open-connections -l model.pkl
```

**Problem: Memory issues with very large logs**
```bash
# Process log files in chunks or use log rotation
# Consider using grep to pre-filter relevant time ranges:
grep "2025-06-10" access.log > filtered.log
389ds-log-analyser src-ip-table -f filtered.log
```

### Debug Mode

Enable debug mode to see detailed parsing information:

```bash
389ds-log-analyser src-ip-table -f access.log --debug
```

This will show:
- Lines that failed to parse
- Parsing errors and exceptions
- Statistics about processed vs. skipped lines

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/theoweiss/389ds-log-analyser.git
cd 389ds-log-analyser

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run type checking (optional)
mypy src/
```

### Code Quality

This project maintains high code quality standards:
- **Type Hints**: All code is fully type-annotated
- **Testing**: Comprehensive test suite with 24+ tests
- **Documentation**: Extensive documentation and examples
- **Code Style**: Consistent formatting and clear naming

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### License Summary

- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Patent use allowed
- ❗ Must include license and copyright notice
- ❗ Must disclose source code
- ❗ Changes must be documented
- ❗ Derivative works must use the same license

## 🙏 Acknowledgments

- Built for the 389 Directory Server community
- Inspired by the need for better LDAP log analysis tools
- Thanks to all contributors and users providing feedback

---

**Need help?** Open an issue on [GitHub](https://github.com/theoweiss/389ds-log-analyser/issues) or check our [documentation](https://github.com/theoweiss/389ds-log-analyser/wiki).



