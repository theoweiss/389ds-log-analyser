# 389ds-log-analyser

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
[![Tests](https://github.com/theoweiss/389ds-log-analyser/actions/workflows/ci.yml/badge.svg)](https://github.com/theoweiss/389ds-log-analyser/actions/workflows/ci.yml)

This project provides a command-line tool to parse and analyze 389 Directory Server access logs. It can identify and report on completed connections, open connections, unindexed searches, and more.

## 💾 Installation

You can install this package directly from GitHub using `pip`:

```bash
pip install git+https://github.com/theoweiss/389ds-log-analyser.git@v1.3.0
```

## 📦 Offline Installation from a Local Clone

If you need to install the package on a machine that does not have internet access, you can do so from a local clone.

### Step 1: On a Machine With Internet Access

First, get a copy of the repository.

```bash
# Clone the repository
git clone https://github.com/theoweiss/389ds-log-analyser.git
```

### Step 2: Transfer to the Offline Machine

Copy the entire `389ds-log-analyser` directory to the offline machine using a USB drive or other method.

### Step 3: On the Offline Machine

Navigate into the project directory and use `pip` to install it. The `--no-deps` flag is important to prevent `pip` from trying to connect to the internet to resolve dependencies.

```bash
cd 389ds-log-analyser
pip install --no-deps .
```

> **Note:** This works because the base package currently has no external dependencies. If dependencies are added in the future, they would need to be downloaded separately on the online machine and transferred along with the project.

## 💻 Usage

The primary command is `389ds-log-analyser`. It requires a log file to be specified with the `-f` or `--file` argument.

```bash
389ds-log-analyser <command> -f <path_to_log_file> [options]

### Shortcut Commands

For convenience, each command is also available as a standalone script. This allows for more direct invocation of a specific query.

- `389ds-src-ip-table`
- `389ds-open-connections`
- `389ds-unique-clients`
- `389ds-unindexed-searches`

**Usage:**
```bash
# Example using the src-ip-table shortcut
389ds-src-ip-table -f <path_to_log_file>
```

### Enabling Command-Line Completion

This project supports command-line completion (tab completion) to help you quickly see available commands and options. To enable it, you first need to activate it for your shell session.

**One-Time Activation:**

Run the following command in your terminal:

```bash
eval "$(register-python-argcomplete 389ds-log-analyser)"
```

After running this, you can type `389ds-log-analyser` followed by a space and press `Tab` to see all available subcommands. This also works for options (e.g., `389ds-log-analyser src-ip-table --<Tab>`).

**Permanent Activation:**

To make the completion permanent, add the command to your shell's startup file (e.g., `~/.bashrc`, `~/.zshrc`):

```bash
echo 'eval "$(register-python-argcomplete 389ds-log-analyser)"' >> ~/.your_shell_startup_file
```

Replace `~/.your_shell_startup_file` with the actual path to your shell's configuration file.

### Resolving Hostnames

The `--resolve-hostnames` flag can be added to any command to resolve IP addresses to their hostnames. This can make the output easier to read, but may slow down the initial query.

When used with a save option (`--save-pickle` or `--save-json`), the resolved hostnames are persisted in the data model. This means you only need to resolve them once, and subsequent loads from the saved file will be fast.

**Usage:**
```bash
389ds-log-analyser src-ip-table -f <log_file> --resolve-hostnames
```

### Filtering by Client IP

The `--filter-client-ip` argument allows you to filter the output to show connections only from one or more specific source IPs. This filter applies to all commands.

**Usage:**
```bash
# Filter for a single IP
389ds-log-analyser src-ip-table -f <log_file> --filter-client-ip 192.168.1.10

# Filter for multiple IPs
389ds-log-analyser src-ip-table -f <log_file> --filter-client-ip 192.168.1.10 192.168.1.11
```

### Persisting the Data Model

For very large log files, parsing can be time-consuming. To speed up subsequent analyses, you can save the parsed data model to a file and load it directly in the future.

#### Saving the Data Model (Pickle Format)

Use the `--save-pickle` or `-p` argument to save the parsed data model to a file using Python's pickle format. This is the fastest method for saving and loading.

**Usage:**
```bash
389ds-log-analyser <command> -f <log_file> -p <datamodel.pkl>
```

#### Saving the Data Model (JSON Format)

Use the `--save-json` or `-j` argument to save the data model in a human-readable JSON format. This is useful for inspecting the data model or for use with other tools.

**Usage:**
```bash
389ds-log-analyser <command> -f <log_file> -j <datamodel.json>
```

**JSON Data Model Structure**

The saved JSON file will contain an object where each key is a connection number. The structure is as follows:

```json
{
  "123": {
    "connection_num": 123,
    "source_ip": "192.168.1.50",
    "source_hostname": "client-a.example.com",
    "destination_ip": "10.0.0.1",
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
      }
    ]
  }
}
```

#### Loading the Data Model

Use the `--load-datamodel` or `-l` argument to load a previously saved data model. The tool will automatically detect the file format (pickle or JSON) based on the file's content and extension. This option is mutually exclusive with the `-f` or `--file` argument.

**Usage:**
```bash
# Load from a pickle file
389ds-log-analyser <command> -l <datamodel.pkl>

# Load from a JSON file
389ds-log-analyser <command> -l <datamodel.json>
```

### 🛠️ Commands


#### Show Completed Connections (`src-ip-table`)

This query displays a table of all connections that have a successful `BIND` and have been closed. The table includes the source IP, bind timestamp, and unbind timestamp.

**Usage:**
```bash
389ds-log-analyser src-ip-table -f <path_to_log_file>
```

**Example Output:**
```
Source IP            Bind Timestamp                      Unbind Timestamp
-------------------- ----------------------------------- -----------------------------------
192.168.1.10         2025-06-10T21:18:06.100000+00:00    2025-06-10T21:18:07.200000+00:00
... 
```

#### Show Open Connections (`open-connections`)

This query displays a table of all connections that have a successful `BIND` but have not yet been closed. This is useful for monitoring currently active sessions.

**Usage:**
```bash
389ds-log-analyser open-connections -f <path_to_log_file>
```

**Example Output:**
```
Source IP            Bind DN                                     Bind Timestamp
-------------------- -------------------------------------------------- -----------------------------------
192.168.1.12         uid=another,ou=people,dc=example,dc=com     2025-06-10T21:18:12.100000+00:00
... 
```

##### Filtering by Bind DN

The `open-connections` command also supports filtering by one or more Bind DNs using the `--filter-bind-dn` argument. This is useful for focusing on connections from specific users or applications.

**Usage:**
```bash
# Filter for a single Bind DN
389ds-log-analyser open-connections -f <log_file> --filter-bind-dn "uid=test,ou=people,dc=example,dc=com"

# Filter for multiple Bind DNs
389ds-log-analyser open-connections -f <log_file> --filter-bind-dn "uid=test,ou=people,dc=example,dc=com" "cn=Directory Manager"
```

When no filter is applied, the command also provides a summary of open connections grouped by Bind DN:

**Example Summary Output:**
```
Summary of Open Connections by Bind DN:
Bind DN                                                                Count
---------------------------------------------------------------------- -----
uid=activeuser,ou=people,dc=example,dc=com                             1
uid=another,ou=people,dc=example,dc=com                                1
```

#### Show Unique Client IPs (`unique-clients`)

This query scans all connections and prints a unique, sorted list of all source IP addresses that have connected to the server.

**Usage:**
```bash
389ds-log-analyser unique-clients -f <path_to_log_file>
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

#### Show Unindexed Searches (`unindexed-searches`)

This query is essential for performance tuning. It identifies and lists all search operations (`SRCH`) that resulted in a `Partially Unindexed Filter` note, which can indicate missing database indexes.

**Usage:**
```bash
389ds-log-analyser unindexed-searches -f <path_to_log_file>
```

**Example Output:**
```
Timestamp                           Conn       Op         Base                           Filter
----------------------------------- ---------- ---------- ------------------------------ ----------------------------------------
2025-06-10T11:06:44.711859+02:00    105        1          dc=example,dc=com              (&(objectClass=ipHost)(ipHostNumber=10.31.50.48))
```



