import subprocess
import sys
import os

# Path to the log file used for testing
LOG_FILE = "test-files/access-comprehensive.log"

def run_command(command, check=True):
    """Helper function to run a command and return the result."""
    # Ensure the src directory is in the python path for subprocesses
    env = os.environ.copy()
    env['PYTHONPATH'] = 'src' + os.pathsep + env.get('PYTHONPATH', '')
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

def test_standalone_script():
    """Tests the standalone '389ds-src-ip-table' script."""
    # Get the path to the script from the virtual environment
    venv_bin = os.path.dirname(sys.executable)
    script_path = os.path.join(venv_bin, '389ds-src-ip-table')
    
    command = [script_path, "-f", LOG_FILE]
    result = run_command(command)
    assert "Source IP            Bind Timestamp                      Unbind Timestamp" in result.stdout
    assert "192.168.1.10" in result.stdout
