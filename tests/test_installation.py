import subprocess
import sys
import tempfile
import venv
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def run_command(command, cwd, check=True):
    """Helper function to run a command and return the result."""
    return subprocess.run(command, capture_output=True, text=True, check=check, cwd=cwd)

def test_package_installation_and_script_execution():
    """
    Tests that the package can be built, installed in a clean venv,
    and that its scripts run correctly.
    """
    with tempfile.TemporaryDirectory() as tempdir:
        temp_path = Path(tempdir)
        venv_path = temp_path / ".venv"

        # 1. Create a clean virtual environment
        venv.create(venv_path, with_pip=True)

        # 2. Build the package from the project root
        run_command([sys.executable, "-m", "build"], cwd=PROJECT_ROOT)

        # 3. Find the built wheel file
        dist_path = PROJECT_ROOT / "dist"
        wheel_files = list(dist_path.glob("*.whl"))
        assert len(wheel_files) > 0, "No wheel file found in dist directory."
        wheel_file = wheel_files[0]

        # 4. Install the package into the clean venv
        pip_executable = venv_path / "bin" / "pip"
        run_command([pip_executable, "install", str(wheel_file)], cwd=temp_path)

        # 5. Run one of the installed scripts from the venv
        script_executable = venv_path / "bin" / "389ds-log-analyser"
        log_file_path = PROJECT_ROOT / "test-files" / "access-comprehensive.log"
        result = run_command([
            script_executable,
            "src-ip-table",
            "-f",
            str(log_file_path)
        ], cwd=temp_path)

        # 6. Check that the script produced the expected output
        assert "Source IP" in result.stdout
        assert "192.168.1.10" in result.stdout
        assert result.returncode == 0
