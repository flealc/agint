import json
import subprocess
from typing import Any


def qmd_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["qmd", "query", query, "--json", "-n", str(limit)],
        check=True,
        capture_output=True,
        text=True,
    )

    parsed = json.loads(result.stdout)

    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict) and "results" in parsed:
        return parsed["results"]

    return [{"raw": parsed}]


def format_qmd_results(results: list[dict[str, Any]], max_chars: int = 4000) -> str:
    chunks = []

    for index, result in enumerate(results, start=1):
        path = (
            result.get("path")
            or result.get("file")
            or result.get("filename")
            or "unknown"
        )
        text = (
            result.get("text")
            or result.get("context")
            or result.get("snippet")
            or str(result)
        )

        chunks.append(f"{index}. {path}\n{text}")

    formatted = "\n\n".join(chunks)

    if len(formatted) > max_chars:
        return formatted[:max_chars] + "\n\n[truncated]"

    return formatted
