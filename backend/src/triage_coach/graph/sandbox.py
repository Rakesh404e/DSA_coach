"""Sandbox runner for executing user code against test cases in an isolated, restricted environment."""

import ast
import base64
import pickle
import subprocess
import sys
from typing import Any

SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "ascii": ascii,
    "bin": bin,
    "bool": bool,
    "bytearray": bytearray,
    "bytes": bytes,
    "callable": callable,
    "chr": chr,
    "complex": complex,
    "dict": dict,
    "divmod": divmod,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "format": format,
    "frozenset": frozenset,
    "getattr": getattr,
    "hasattr": hasattr,
    "hash": hash,
    "hex": hex,
    "id": id,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "object": object,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "range": range,
    "repr": repr,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
    "True": True,
    "False": False,
    "None": None,
    "Exception": Exception,
    "ValueError": ValueError,
    "TypeError": TypeError,
    "IndexError": IndexError,
    "KeyError": KeyError,
    "ZeroDivisionError": ZeroDivisionError,
    "StopIteration": StopIteration,
    "AssertionError": AssertionError,
    "AttributeError": AttributeError,
    "OverflowError": OverflowError,
    "ArithmeticError": ArithmeticError,
    "LookupError": LookupError,
    "RuntimeError": RuntimeError,
    "print": lambda *args, **kwargs: None,
}

_WORKER_CODE = """
import ast
import base64
import pickle
import sys

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "ascii": ascii, "bin": bin, "bool": bool,
    "bytearray": bytearray, "bytes": bytes, "callable": callable, "chr": chr,
    "complex": complex, "dict": dict, "divmod": divmod, "enumerate": enumerate,
    "filter": filter, "float": float, "format": format, "frozenset": frozenset,
    "getattr": getattr, "hasattr": hasattr, "hash": hash, "hex": hex, "id": id,
    "int": int, "isinstance": isinstance, "issubclass": issubclass, "iter": iter,
    "len": len, "list": list, "map": map, "max": max, "min": min, "next": next,
    "object": object, "oct": oct, "ord": ord, "pow": pow, "range": range,
    "repr": repr, "reversed": reversed, "round": round, "set": set, "slice": slice,
    "sorted": sorted, "str": str, "sum": sum, "tuple": tuple, "type": type, "zip": zip,
    "True": True, "False": False, "None": None, "Exception": Exception,
    "ValueError": ValueError, "TypeError": TypeError, "IndexError": IndexError,
    "KeyError": KeyError, "ZeroDivisionError": ZeroDivisionError,
    "StopIteration": StopIteration, "AssertionError": AssertionError,
    "AttributeError": AttributeError, "OverflowError": OverflowError,
    "ArithmeticError": ArithmeticError, "LookupError": LookupError,
    "RuntimeError": RuntimeError, "print": lambda *args, **kwargs: None,
}

def execute():
    try:
        raw = sys.stdin.read()
        code, test_case, entrypoint = pickle.loads(base64.b64decode(raw))
    except Exception as e:
        res = {"passed": False, "actual_output": None, "error": f"PayloadError: {e}"}
        sys.stdout.write(base64.b64encode(pickle.dumps(res)).decode("ascii"))
        return

    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ImportError("Imports are not permitted in the sandbox.")

        namespace = {"__builtins__": SAFE_BUILTINS}
        exec(code, namespace)

        target_fn = None
        if entrypoint and entrypoint in namespace and callable(namespace[entrypoint]):
            target_fn = namespace[entrypoint]
        else:
            candidates = [
                v for k, v in namespace.items()
                if callable(v) and k not in SAFE_BUILTINS and not k.startswith("__")
            ]
            if candidates:
                target_fn = candidates[-1]

        if target_fn is None:
            raise NameError("No executable function found in submitted code.")

        args = test_case.get("input")
        if isinstance(args, tuple):
            actual = target_fn(*args)
        elif isinstance(args, dict):
            actual = target_fn(**args)
        else:
            actual = target_fn(args)

        expected = test_case.get("expected_output")
        passed = bool(actual == expected)
        res = {"passed": passed, "actual_output": actual, "error": None}
    except BaseException as e:
        res = {"passed": False, "actual_output": None, "error": f"{type(e).__name__}: {e}"}

    sys.stdout.write(base64.b64encode(pickle.dumps(res)).decode("ascii"))

if __name__ == "__main__":
    execute()
"""


def _check_code_preconditions(code: str) -> str | None:
    """Perform pre-execution checks on code for syntax errors and forbidden imports."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"
    except Exception as e:
        return f"CodeParseError: {e}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return "ImportError: Imports are not permitted in the sandbox."
    return None


def run_against_tests(
    code: str,
    test_cases: list,
    timeout: float = 2.0,
    entrypoint: str | None = None,
) -> list[dict]:
    """Execute submitted code against test cases in an isolated subprocess sandbox.

    Enforces:
    - Restricted builtins namespace (no __import__, no os, no open, no network).
    - Hard wall-clock timeout per test case via subprocess.run(..., timeout=timeout).
    - Exception safety: never lets an exception propagate out of this function.

    Returns:
        list of dicts with shape:
        {"test_case": test_case, "passed": bool, "actual_output": Any, "error": str | None}
    """
    results: list[dict] = []

    try:
        # Pre-check code for syntax errors or disallowed import statements
        pre_error = _check_code_preconditions(code)
        if pre_error:
            for tc in test_cases:
                results.append({
                    "test_case": tc,
                    "passed": False,
                    "actual_output": None,
                    "error": pre_error,
                })
            return results

        # Run each test case in an isolated subprocess with timeout
        for tc in test_cases:
            payload = base64.b64encode(
                pickle.dumps((code, tc, entrypoint))
            ).decode("ascii")

            try:
                proc = subprocess.run(
                    [sys.executable, "-c", _WORKER_CODE],
                    input=payload,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                )

                if proc.returncode == 0 and proc.stdout.strip():
                    worker_res = pickle.loads(base64.b64decode(proc.stdout.strip()))
                    results.append({
                        "test_case": tc,
                        "passed": bool(worker_res.get("passed", False)),
                        "actual_output": worker_res.get("actual_output"),
                        "error": worker_res.get("error"),
                    })
                else:
                    err_text = proc.stderr.strip() if proc.stderr else f"Process exited with code {proc.returncode}"
                    results.append({
                        "test_case": tc,
                        "passed": False,
                        "actual_output": None,
                        "error": err_text,
                    })
            except subprocess.TimeoutExpired:
                results.append({
                    "test_case": tc,
                    "passed": False,
                    "actual_output": None,
                    "error": f"Execution timed out after {timeout} seconds",
                })
            except Exception as ex:
                results.append({
                    "test_case": tc,
                    "passed": False,
                    "actual_output": None,
                    "error": f"{type(ex).__name__}: {ex}",
                })
    except Exception as fatal_ex:
        # Guarantee that exceptions never propagate out
        for tc in test_cases:
            results.append({
                "test_case": tc,
                "passed": False,
                "actual_output": None,
                "error": f"FatalSandboxError: {fatal_ex}",
            })

    return results
