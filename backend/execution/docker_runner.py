import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_TIMEOUT = 5
MAX_OUTPUT_SIZE = 10_000


def run_python_code_fallback(
    code: str,
    timeout: int = DEFAULT_TIMEOUT,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        code_file = workspace / "main.py"
        code_file.write_text(code, encoding="utf-8")

        try:
            process = subprocess.run(
                [sys.executable, str(code_file)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(workspace),
            )

            stdout = (process.stdout or "")[:MAX_OUTPUT_SIZE]
            stderr = (process.stderr or "")[:MAX_OUTPUT_SIZE]

            return {
                "success": process.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode,
                "timed_out": False,
            }

        except subprocess.TimeoutExpired as error:
            return {
                "success": False,
                "stdout": (error.stdout or "")[:MAX_OUTPUT_SIZE],
                "stderr": (error.stderr or "")[:MAX_OUTPUT_SIZE],
                "exit_code": None,
                "timed_out": True,
            }


def run_python_code(
    code: str,
    timeout: int = DEFAULT_TIMEOUT,
):
    with tempfile.TemporaryDirectory() as temp_dir:

        workspace = Path(temp_dir)

        code_file = workspace / "main.py"

        code_file.write_text(
            code,
            encoding="utf-8",
        )

        command = [
            "docker",
            "run",
            "--rm",

            # No network access
            "--network",
            "none",

            # Memory limit
            "--memory",
            "128m",

            # CPU limit
            "--cpus",
            "0.5",

            # Limit number of processes
            "--pids-limit",
            "32",

            # Read-only container filesystem
            "--read-only",

            # Temporary writable filesystem
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",

            # Mount only the execution workspace
            "--mount",
            (
                f"type=bind,"
                f"source={workspace.resolve()},"
                f"target=/workspace,"
                f"readonly"
            ),

            # Working directory
            "--workdir",
            "/workspace",

            "ai-python-runner",

            "python",
            "main.py",
        ]

        try:

            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            stdout = process.stdout[:MAX_OUTPUT_SIZE]
            stderr = process.stderr[:MAX_OUTPUT_SIZE]

            if process.returncode != 0 and any(msg in stderr.lower() for msg in ["cannot connect to the docker daemon", "failed to connect to the docker api", "docker: error", "unable to find image", "error during connect"]):
                return run_python_code_fallback(code, timeout=timeout)

            return {
                "success": process.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": process.returncode,
                "timed_out": False,
            }

        except subprocess.TimeoutExpired as error:

            return {
                "success": False,
                "stdout": (
                    error.stdout or ""
                )[:MAX_OUTPUT_SIZE],
                "stderr": (
                    error.stderr or ""
                )[:MAX_OUTPUT_SIZE],
                "exit_code": None,
                "timed_out": True,
            }

        except FileNotFoundError:

            return run_python_code_fallback(code, timeout=timeout)
