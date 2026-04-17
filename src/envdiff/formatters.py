"""Output formatting for diff and check results."""

from __future__ import annotations

import json
from typing import IO

from rich.console import Console
from rich.table import Table

from .diff import CheckResult, DiffResult


def _redact(value: str) -> str:
    if value == "":
        return "<empty>"
    return "<set>"


def _display(value: str, show_values: bool) -> str:
    if show_values:
        return value
    return _redact(value)


def render_diff_table(
    result: DiffResult,
    a: dict[str, str],
    b: dict[str, str],
    name_a: str,
    name_b: str,
    show_values: bool,
    console: Console,
) -> None:
    table = Table(title=f"envdiff: {name_a} vs {name_b}", show_lines=False)
    table.add_column("Key", style="bold")
    table.add_column("Status")
    table.add_column(name_a, overflow="fold")
    table.add_column(name_b, overflow="fold")

    for k in result.only_in_a:
        table.add_row(k, "[red]only in A[/red]", _display(a[k], show_values), "—")
    for k in result.only_in_b:
        table.add_row(k, "[red]only in B[/red]", "—", _display(b[k], show_values))
    for k in result.different:
        table.add_row(
            k,
            "[yellow]different[/yellow]",
            _display(a[k], show_values),
            _display(b[k], show_values),
        )

    if not result.has_differences:
        console.print(f"[green]No differences between {name_a} and {name_b}.[/green]")
        return

    console.print(table)
    console.print(
        f"Summary: [red]{len(result.only_in_a)}[/red] only in A, "
        f"[red]{len(result.only_in_b)}[/red] only in B, "
        f"[yellow]{len(result.different)}[/yellow] differing, "
        f"[green]{len(result.same)}[/green] matching."
    )


def diff_to_json(
    result: DiffResult,
    a: dict[str, str],
    b: dict[str, str],
    show_values: bool,
) -> str:
    def v(d: dict[str, str], k: str) -> str:
        return d[k] if show_values else _redact(d[k])

    payload = {
        "only_in_a": {k: v(a, k) for k in result.only_in_a},
        "only_in_b": {k: v(b, k) for k in result.only_in_b},
        "different": {
            k: {"a": v(a, k), "b": v(b, k)} for k in result.different
        },
        "same": result.same,
        "has_differences": result.has_differences,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def render_check_table(
    result: CheckResult,
    target_name: str,
    example_name: str,
    console: Console,
) -> None:
    table = Table(title=f"envdiff check: {target_name} against {example_name}")
    table.add_column("Key", style="bold")
    table.add_column("Issue")
    for k in result.missing:
        table.add_row(k, "[red]missing[/red]")
    for k in result.empty:
        table.add_row(k, "[yellow]empty[/yellow]")
    for k in result.extra:
        table.add_row(k, "[cyan]extra (not in example)[/cyan]")

    if not (result.missing or result.empty or result.extra):
        console.print(f"[green]{target_name} matches {example_name} perfectly.[/green]")
        return

    console.print(table)
    if result.missing:
        console.print(
            f"[red]{len(result.missing)} missing key(s)[/red] — target is incomplete."
        )
    if result.empty:
        console.print(f"[yellow]{len(result.empty)} empty value(s).[/yellow]")
    if result.extra:
        console.print(f"[cyan]{len(result.extra)} extra key(s).[/cyan]")


def check_to_json(result: CheckResult) -> str:
    return json.dumps(
        {
            "missing": result.missing,
            "empty": result.empty,
            "extra": result.extra,
            "ok": result.ok,
        },
        indent=2,
        sort_keys=True,
    )


def list_to_text(keys: list[str], values: dict[str, str], show_values: bool) -> str:
    lines = []
    for k in keys:
        if show_values:
            lines.append(f"{k}={values[k]}")
        else:
            lines.append(f"{k}={_redact(values[k])}")
    return "\n".join(lines)


def list_to_json(keys: list[str], values: dict[str, str], show_values: bool) -> str:
    if show_values:
        return json.dumps({k: values[k] for k in keys}, indent=2, sort_keys=True)
    return json.dumps(
        {k: _redact(values[k]) for k in keys}, indent=2, sort_keys=True
    )
