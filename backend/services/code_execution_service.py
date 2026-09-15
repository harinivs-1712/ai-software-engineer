from execution.docker_runner import run_python_code


MAX_CODE_LENGTH = 20_000
MAX_TIMEOUT = 10


def execute_python(
    code: str,
    timeout: int = 5,
):
    if not isinstance(code, str):
        return {
            "success": False,
            "error": "Code must be a string.",
        }

    if not code.strip():
        return {
            "success": False,
            "error": "Code cannot be empty.",
        }

    if len(code) > MAX_CODE_LENGTH:
        return {
            "success": False,
            "error": (
                "Code exceeds the maximum allowed "
                "size of 20,000 characters."
            ),
        }

    timeout = min(
        max(timeout, 1),
        MAX_TIMEOUT,
    )

    result = run_python_code(
        code=code,
        timeout=timeout,
    )

    res = {
        "language": "python",
        "code": code,
        "success": result["success"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "exit_code": result["exit_code"],
        "timed_out": result["timed_out"],
    }

    if result.get("timed_out"):
        res["error"] = f"Execution timed out after {timeout} seconds."

    return res
