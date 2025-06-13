import io
import os
import socket
import subprocess
import sys
import pytest
from contextlib import redirect_stdout
from unittest.mock import patch

from cli import print_unique_clients

# Path to the log file used for testing
LOG_FILE = "test-files/access-comprehensive.log"

def run_command(command, check=True):
    """Helper function to run a command and return the result."""
    # Ensure the project root is in the python path for subprocesses so `src.` imports work
    env = os.environ.copy()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')
    return subprocess.run(command, capture_output=True, text=True, check=check, env=env)

def test_src_ip_table_subcommand():
    """Tests the 'src-ip-table' subcommand."""
    command = [
        sys.executable,  # Use the same python interpreter that runs pytest
        "-m", "cli",
        "src-ip-table",
        "-f", LOG_FILE
    ]
    result = run_command(command)
    
    assert "Source IP            Bind Timestamp                      Unbind Timestamp" in result.stdout
    assert "192.168.1.10" in result.stdout

def test_open_connections_subcommand():
    """Tests the 'open-connections' subcommand."""
    command = [sys.executable, "-m", "cli", "open-connections", "-f", LOG_FILE]
    result = run_command(command)
    assert "Source IP            Bind DN                                            Bind Timestamp" in result.stdout
    assert "192.168.1.12" in result.stdout

def test_unique_clients_subcommand():
    """Tests the 'unique-clients' subcommand."""
    command = [sys.executable, "-m", "cli", "unique-clients", "-f", LOG_FILE]
    result = run_command(command)
    assert "Unique Client IPs" in result.stdout
    assert "192.168.1.13" in result.stdout

def test_unindexed_searches_subcommand():
    """Tests the 'unindexed-searches' subcommand."""
    command = [sys.executable, "-m", "cli", "unindexed-searches", "-f", LOG_FILE]
    result = run_command(command)
    assert "Timestamp                           Conn       Op         Base" in result.stdout
    assert "(&(objectClass=ipHost)(ipHostNumber=10.31.50.48))" in result.stdout

def test_filter_client_ip():
    """Tests the '--filter-client-ip' argument."""
    command = [
        sys.executable, "-m", "cli",
        "src-ip-table",
        "-f", LOG_FILE,
        "--filter-client-ip", "192.168.1.11"
    ]
    result = run_command(command)
    assert "192.168.1.11" in result.stdout
    assert "192.168.1.10" not in result.stdout

def test_hostname_resolution():
    """Tests that hostname resolution works correctly as a unit test."""
    # Create a dummy Connection object to simulate the data model
    class MockConnection:
        def __init__(self, ip):
            self.source_ip = ip

    connections = {
        1: MockConnection("192.168.1.10"),
        2: MockConnection("192.168.1.11"),
    }

    # Mock the socket call to simulate DNS lookups
    with patch('cli.socket.gethostbyaddr') as mock_gethostbyaddr:
        # Return a different hostname depending on the IP looked up
        def side_effect(ip):
            if ip == "192.168.1.10":
                return ("host1.example.com", [], [ip])
            if ip == "192.168.1.11":
                return ("host2.example.com", [], [ip])
            raise socket.herror("Not found")
        mock_gethostbyaddr.side_effect = side_effect

        # Capture the output of the print function
        string_io = io.StringIO()
        with redirect_stdout(string_io):
            print_unique_clients(connections, resolve_hostnames=True)
        output = string_io.getvalue()

    assert "host1.example.com" in output
    assert "host2.example.com" in output
    assert "192.168.1.10" not in output

@pytest.mark.parametrize("script_name", [
    "389ds-src-ip-table",
    "389ds-open-connections",
    "389ds-unique-clients",
    "389ds-unindexed-searches",
])
def test_standalone_scripts(script_name):
    """Tests the standalone command-line scripts."""
    venv_bin = os.path.dirname(sys.executable)
    script_path = os.path.join(venv_bin, script_name)

    command = [script_path, "-f", LOG_FILE]
    result = run_command(command)

    # Simple check to ensure the script runs and produces some output
    assert result.returncode == 0
    assert len(result.stdout) > 0
