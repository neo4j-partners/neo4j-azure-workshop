"""
Test runner for workshop solutions across multiple environments.
"""

import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from .config import DEPLOYMENTS_DIR, PROJECT_ROOT, TOKEN_USAGE_DIR, TOKEN_USAGE_FILE
from .state import parse_env_file


class TestResult:
    """Result of a single environment test run."""

    def __init__(
        self,
        env_name: str,
        success: bool,
        duration: float,
        output: str,
        solutions_run: list[str],
    ):
        self.env_name = env_name
        self.success = success
        self.duration = duration
        self.output = output
        self.solutions_run = solutions_run


def run_single_test(
    env_name: str,
    env_file: Path,
    solution: str,
    log_dir: Path,
) -> TestResult:
    """
    Run test for a single environment.

    Writes output to a log file and returns the result.
    """
    env_vars = parse_env_file(env_file)
    # Set TOKEN_USAGE_ENV so each process writes to its own file
    env_vars["TOKEN_USAGE_ENV"] = env_name
    # Use PYTHONUNBUFFERED to get real-time output
    env_vars["PYTHONUNBUFFERED"] = "1"

    start_time = time.time()
    log_file = log_dir / f"{env_name}.log"

    with open(log_file, "w") as f:
        f.write(f"=== {env_name} started at {datetime.now().isoformat()} ===\n")
        f.write(f"Solution: {solution}\n")
        f.write(f"{'=' * 60}\n\n")
        f.flush()

        result = subprocess.run(
            ["uv", "run", "python", "new-workshops/main.py", solution],
            cwd=PROJECT_ROOT,
            env=env_vars,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
        )

    duration = time.time() - start_time
    output = log_file.read_text()

    # Append completion status
    with open(log_file, "a") as f:
        f.write(f"\n{'=' * 60}\n")
        status = "SUCCESS" if result.returncode == 0 else "FAILED"
        f.write(f"=== {env_name} {status} in {duration:.1f}s ===\n")

    # Extract which solutions were run from output
    solutions_run = []
    for line in output.splitlines():
        if line.startswith(">>> Running:"):
            sol_name = line.replace(">>> Running:", "").strip()
            solutions_run.append(sol_name)

    return TestResult(
        env_name=env_name,
        success=result.returncode == 0,
        duration=duration,
        output=output,
        solutions_run=solutions_run,
    )


def run_parallel_tests(
    test_jobs: list[tuple[str, Path]],
    solution: str,
    max_workers: int,
) -> list[TestResult]:
    """
    Run tests in parallel across multiple environments.

    Args:
        test_jobs: List of (env_name, env_file) tuples
        solution: Solution number to run
        max_workers: Maximum parallel tests

    Returns:
        List of TestResult objects
    """
    log_dir = DEPLOYMENTS_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clean old logs
    for old_log in log_dir.glob("*.log"):
        old_log.unlink()

    print(f"Logs: {log_dir}/")
    print(f"  Monitor progress: tail -f {log_dir}/*.log")
    print(f"  Or watch one:     tail -f {log_dir}/workshop-01.log\n")

    results: list[TestResult] = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_test, env_name, env_file, solution, log_dir): env_name
            for env_name, env_file in test_jobs
        }

        running = set(env_name for env_name, _ in test_jobs)
        completed = 0

        for future in as_completed(futures):
            completed += 1
            env_name = futures[future]
            running.discard(env_name)

            try:
                result = future.result()
                results.append(result)
                _print_test_progress(result, completed, len(test_jobs), start_time, running)
            except Exception as e:
                results.append(TestResult(env_name, False, 0.0, str(e), []))
                print(f"  \033[91m✗\033[0m [{completed}/{len(test_jobs)}] {env_name} error: {e}")

    return results


def _print_test_progress(
    result: TestResult,
    completed: int,
    total: int,
    start_time: float,
    running: set[str],
) -> None:
    """Print progress for a completed test."""
    status = "✓" if result.success else "✗"
    color = "\033[92m" if result.success else "\033[91m"
    reset = "\033[0m"
    solutions_str = f" [{len(result.solutions_run)} solutions]" if result.solutions_run else ""
    elapsed = time.time() - start_time

    print(
        f"  {color}{status}{reset} [{completed}/{total}] "
        f"{result.env_name} ({result.duration:.1f}s){solutions_str} "
        f"[elapsed: {elapsed:.0f}s]"
    )

    if running and len(running) <= 5:
        print(f"      Still running: {', '.join(sorted(running))}")


def print_test_summary(results: list[TestResult]) -> None:
    """Print summary of test results."""
    results.sort(key=lambda x: x.env_name)

    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    total_time = max(r.duration for r in results) if results else 0

    print(f"\n{'=' * 60}")
    print("RESULTS")
    print(f"{'=' * 60}")

    for result in results:
        status = "✓" if result.success else "✗"
        color = "\033[92m" if result.success else "\033[91m"
        reset = "\033[0m"
        solutions_count = f"[{len(result.solutions_run)} solutions]" if result.solutions_run else ""
        print(f"  {color}{status}{reset} {result.env_name:<20} ({result.duration:.1f}s) {solutions_count}")

    # Show which solutions were run
    all_solutions: set[str] = set()
    for r in results:
        all_solutions.update(r.solutions_run)
    if all_solutions:
        print(f"\nSolutions tested: {', '.join(sorted(all_solutions))}")

    print(f"\n{'-' * 60}")
    print(f"PASSED: {passed} | FAILED: {failed} | Total time: {total_time:.1f}s")

    # Show failure details
    failures = [r for r in results if not r.success]
    for result in failures:
        print(f"\n{'=' * 60}")
        print(f"FAILURE DETAILS: {result.env_name}")
        if result.solutions_run:
            print(f"Solutions completed before failure: {', '.join(result.solutions_run)}")
        print(f"{'=' * 60}")
        # Show last 30 lines of output
        lines = result.output.strip().split("\n")
        if len(lines) > 30:
            print("... (truncated)")
            lines = lines[-30:]
        for line in lines:
            print(f"  {line}")


def merge_token_usage_files() -> None:
    """Merge per-environment token usage files into the main token_usage.json."""
    if not TOKEN_USAGE_DIR.exists():
        return

    # Load existing main file or create empty structure
    if TOKEN_USAGE_FILE.exists():
        try:
            merged = json.loads(TOKEN_USAGE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            merged = _empty_token_usage()
    else:
        merged = _empty_token_usage()

    # Ensure failures key exists
    if "failures" not in merged:
        merged["failures"] = []

    # Merge each environment file
    env_files = list(TOKEN_USAGE_DIR.glob("*.json"))
    if not env_files:
        return

    print(f"\nMerging token usage from {len(env_files)} environment(s)...")

    for env_file in env_files:
        try:
            env_data = json.loads(env_file.read_text())
            env_name = env_file.stem

            # Add environment name to each session
            for session in env_data.get("sessions", []):
                session["environment"] = env_name
                merged["sessions"].append(session)

            # Add environment name to each failure
            for failure in env_data.get("failures", []):
                failure["environment"] = env_name
                merged["failures"].append(failure)

            # Add totals
            env_totals = env_data.get("totals", {})
            merged["totals"]["llm_input"] += env_totals.get("llm_input", 0)
            merged["totals"]["llm_output"] += env_totals.get("llm_output", 0)
            merged["totals"]["embedding"] += env_totals.get("embedding", 0)

            # Remove the per-environment file after merging
            env_file.unlink()
        except (json.JSONDecodeError, OSError) as e:
            print(f"  Warning: Could not merge {env_file.name}: {e}")

    # Save merged file
    TOKEN_USAGE_FILE.write_text(json.dumps(merged, indent=2))

    # Remove directory if empty
    try:
        TOKEN_USAGE_DIR.rmdir()
    except OSError:
        pass

    print(f"  Merged into: {TOKEN_USAGE_FILE}")


def _empty_token_usage() -> dict:
    """Return empty token usage structure."""
    return {
        "sessions": [],
        "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0},
        "failures": [],
    }
