#!/usr/bin/env python3
"""
Token Usage Report Generator

Reads the token_usage.json file and produces a detailed report of token
consumption across all workshop solution scripts, including LLM call timing.

Usage:
    uv run python solutions/token_report.py           # Show report
    uv run python solutions/token_report.py --reset   # Reset all counts
    uv run python solutions/token_report.py --json    # Output raw JSON
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

TOKEN_USAGE_FILE = Path(__file__).parent / "token_usage.json"


def load_usage() -> dict:
    """Load token usage data from JSON file."""
    if not TOKEN_USAGE_FILE.exists():
        return {"sessions": [], "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0}}
    try:
        return json.loads(TOKEN_USAGE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"sessions": [], "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0}}


def reset_usage() -> None:
    """Reset all token usage data."""
    TOKEN_USAGE_FILE.write_text(json.dumps({
        "sessions": [],
        "totals": {"llm_input": 0, "llm_output": 0, "embedding": 0},
    }, indent=2))
    print("Token usage has been reset.")


def format_number(n: int) -> str:
    """Format number with thousands separator."""
    return f"{n:,}"


def format_ms(ms: float) -> str:
    """Format milliseconds nicely."""
    if ms >= 1000:
        return f"{ms/1000:.2f}s"
    return f"{ms:.0f}ms"


def calculate_percentile(values: list[float], percentile: float) -> float:
    """Calculate the given percentile from a sorted list of values."""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    index = min(index, len(sorted_values) - 1)
    return sorted_values[index]


def generate_report(data: dict) -> str:
    """Generate a formatted token usage report."""
    lines = []
    lines.append("=" * 70)
    lines.append("TOKEN USAGE REPORT")
    lines.append("=" * 70)

    totals = data.get("totals", {})
    sessions = data.get("sessions", [])

    # Overall totals
    llm_input = totals.get("llm_input", 0)
    llm_output = totals.get("llm_output", 0)
    embedding = totals.get("embedding", 0)
    total = llm_input + llm_output + embedding

    lines.append("")
    lines.append("OVERALL TOTALS")
    lines.append("-" * 40)
    lines.append(f"  LLM Input Tokens:     {format_number(llm_input):>12}")
    lines.append(f"  LLM Output Tokens:    {format_number(llm_output):>12}")
    lines.append(f"  Embedding Tokens:     {format_number(embedding):>12}")
    lines.append(f"  {'─' * 28}")
    lines.append(f"  TOTAL TOKENS:         {format_number(total):>12}")

    if not sessions:
        lines.append("")
        lines.append("No individual sessions recorded yet.")
        lines.append("")
        return "\n".join(lines)

    # Collect LLM timing data
    llm_durations = []
    script_durations = defaultdict(list)

    for session in sessions:
        if session.get("type") == "llm" and "duration_ms" in session:
            duration = session["duration_ms"]
            llm_durations.append(duration)
            script = session.get("script", "unknown")
            script_durations[script].append(duration)

    # LLM Timing Statistics
    if llm_durations:
        lines.append("")
        lines.append("LLM CALL TIMING")
        lines.append("-" * 40)
        avg_ms = sum(llm_durations) / len(llm_durations)
        min_ms = min(llm_durations)
        max_ms = max(llm_durations)
        p99_ms = calculate_percentile(llm_durations, 99)

        lines.append(f"  Total LLM Calls:      {len(llm_durations):>12}")
        lines.append(f"  Average:              {format_ms(avg_ms):>12}")
        lines.append(f"  Min:                  {format_ms(min_ms):>12}")
        lines.append(f"  Max:                  {format_ms(max_ms):>12}")
        lines.append(f"  P99:                  {format_ms(p99_ms):>12}")

    # Breakdown by script
    script_usage = defaultdict(lambda: {"llm_input": 0, "llm_output": 0, "embedding": 0, "calls": 0})
    model_usage = defaultdict(lambda: {"tokens": 0, "calls": 0})

    for session in sessions:
        script = session.get("script", "unknown")
        model = session.get("model", "unknown")
        session_type = session.get("type", "unknown")

        script_usage[script]["calls"] += 1
        model_usage[model]["calls"] += 1

        if session_type == "llm":
            input_tokens = session.get("input_tokens", 0)
            output_tokens = session.get("output_tokens", 0)
            script_usage[script]["llm_input"] += input_tokens
            script_usage[script]["llm_output"] += output_tokens
            model_usage[model]["tokens"] += input_tokens + output_tokens
        elif session_type == "embedding":
            tokens = session.get("tokens", 0)
            script_usage[script]["embedding"] += tokens
            model_usage[model]["tokens"] += tokens

    # By Script
    lines.append("")
    lines.append("USAGE BY SCRIPT")
    lines.append("-" * 70)
    lines.append(f"{'Script':<35} {'LLM In':>10} {'LLM Out':>10} {'Embed':>10}")
    lines.append("-" * 70)

    for script in sorted(script_usage.keys()):
        usage = script_usage[script]
        lines.append(
            f"{script:<35} "
            f"{format_number(usage['llm_input']):>10} "
            f"{format_number(usage['llm_output']):>10} "
            f"{format_number(usage['embedding']):>10}"
        )

    # Timing by Script (if we have timing data)
    if script_durations:
        lines.append("")
        lines.append("TIMING BY SCRIPT")
        lines.append("-" * 70)
        lines.append(f"{'Script':<35} {'Calls':>6} {'Avg':>10} {'Min':>10} {'Max':>10}")
        lines.append("-" * 70)

        for script in sorted(script_durations.keys()):
            durations = script_durations[script]
            avg = sum(durations) / len(durations)
            lines.append(
                f"{script:<35} "
                f"{len(durations):>6} "
                f"{format_ms(avg):>10} "
                f"{format_ms(min(durations)):>10} "
                f"{format_ms(max(durations)):>10}"
            )

    # By Model
    lines.append("")
    lines.append("USAGE BY MODEL")
    lines.append("-" * 50)
    lines.append(f"{'Model':<30} {'Tokens':>12} {'Calls':>6}")
    lines.append("-" * 50)

    for model in sorted(model_usage.keys()):
        usage = model_usage[model]
        lines.append(f"{model:<30} {format_number(usage['tokens']):>12} {usage['calls']:>6}")

    # By Environment (if environment data is present)
    env_usage = defaultdict(lambda: {"llm_input": 0, "llm_output": 0, "embedding": 0, "calls": 0})
    has_env_data = False

    for session in sessions:
        env = session.get("environment")
        if env:
            has_env_data = True
            env_usage[env]["calls"] += 1
            if session.get("type") == "llm":
                env_usage[env]["llm_input"] += session.get("input_tokens", 0)
                env_usage[env]["llm_output"] += session.get("output_tokens", 0)
            elif session.get("type") == "embedding":
                env_usage[env]["embedding"] += session.get("tokens", 0)

    if has_env_data:
        lines.append("")
        lines.append("USAGE BY ENVIRONMENT")
        lines.append("-" * 70)
        lines.append(f"{'Environment':<20} {'LLM In':>10} {'LLM Out':>10} {'Embed':>10} {'Calls':>8}")
        lines.append("-" * 70)

        for env in sorted(env_usage.keys()):
            usage = env_usage[env]
            lines.append(
                f"{env:<20} "
                f"{format_number(usage['llm_input']):>10} "
                f"{format_number(usage['llm_output']):>10} "
                f"{format_number(usage['embedding']):>10} "
                f"{usage['calls']:>8}"
            )

    # Recent activity
    lines.append("")
    lines.append("RECENT ACTIVITY (last 10 calls)")
    lines.append("-" * 70)

    recent = sessions[-10:] if len(sessions) > 10 else sessions
    for session in reversed(recent):
        timestamp = session.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        session_type = session.get("type", "?")
        script = session.get("script", "unknown")
        duration_str = ""

        if session_type == "llm":
            tokens = session.get("input_tokens", 0) + session.get("output_tokens", 0)
            if "duration_ms" in session:
                duration_str = f" ({format_ms(session['duration_ms'])})"
            lines.append(f"  {timestamp}  LLM   {script:<20} {format_number(tokens):>8} tokens{duration_str}")
        else:
            tokens = session.get("tokens", 0)
            lines.append(f"  {timestamp}  EMBED {script:<20} {format_number(tokens):>8} tokens")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Data file: {TOKEN_USAGE_FILE}")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Token usage report generator")
    parser.add_argument("--reset", action="store_true", help="Reset all token counts")
    parser.add_argument("--json", action="store_true", help="Output raw JSON data")
    args = parser.parse_args()

    if args.reset:
        reset_usage()
        return

    data = load_usage()

    if args.json:
        print(json.dumps(data, indent=2))
        return

    print(generate_report(data))


if __name__ == "__main__":
    main()
