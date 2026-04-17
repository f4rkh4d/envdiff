"""envdiff command-line interface."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .diff import check_against_example, diff_envs
from .formatters import (
    check_to_json,
    diff_to_json,
    list_to_json,
    list_to_text,
    render_check_table,
    render_diff_table,
)
from .parser import ParseError, parse_file


def _load(path: str) -> dict[str, str]:
    try:
        return parse_file(path)
    except FileNotFoundError:
        raise click.ClickException(f"File not found: {path}")
    except ParseError as e:
        raise click.ClickException(f"Parse error in {path}: {e}")


@click.group(help="Compare and validate .env files.")
@click.version_option(__version__, prog_name="envdiff")
def main() -> None:
    pass


@main.command("diff", help="Show differences between two env files.")
@click.argument("file_a", type=click.Path(exists=True, dir_okay=False))
@click.argument("file_b", type=click.Path(exists=True, dir_okay=False))
@click.option("--show-values", is_flag=True, help="Reveal values instead of redacting.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output.")
def diff_cmd(file_a: str, file_b: str, show_values: bool, as_json: bool) -> None:
    a = _load(file_a)
    b = _load(file_b)
    result = diff_envs(a, b)
    if as_json:
        click.echo(diff_to_json(result, a, b, show_values))
    else:
        console = Console()
        render_diff_table(
            result, a, b, Path(file_a).name, Path(file_b).name, show_values, console
        )
    if result.has_differences:
        sys.exit(1)


@main.command("check", help="Validate env file against an example.")
@click.argument("envfile", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--example",
    "example",
    required=True,
    type=click.Path(exists=True, dir_okay=False),
    help="Path to .env.example file.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output.")
@click.option(
    "--strict",
    is_flag=True,
    help="Also fail on extra keys not present in example.",
)
def check_cmd(envfile: str, example: str, as_json: bool, strict: bool) -> None:
    target = _load(envfile)
    ex = _load(example)
    result = check_against_example(target, ex)
    if as_json:
        click.echo(check_to_json(result))
    else:
        console = Console()
        render_check_table(result, Path(envfile).name, Path(example).name, console)
    fail = bool(result.missing) or (strict and bool(result.extra))
    if fail:
        sys.exit(1)


@main.command("list", help="List keys in an env file.")
@click.argument("envfile", type=click.Path(exists=True, dir_okay=False))
@click.option("--show-values", is_flag=True, help="Reveal values instead of redacting.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON output.")
def list_cmd(envfile: str, show_values: bool, as_json: bool) -> None:
    values = _load(envfile)
    keys = sorted(values)
    if as_json:
        click.echo(list_to_json(keys, values, show_values))
    else:
        click.echo(list_to_text(keys, values, show_values))


if __name__ == "__main__":
    main()
