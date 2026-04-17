import json
from pathlib import Path

from click.testing import CliRunner

from envdiff.cli import main


def write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def test_cli_diff_no_differences(tmp_path):
    a = write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = write(tmp_path, "b.env", "FOO=1\nBAR=2\n")
    result = CliRunner().invoke(main, ["diff", str(a), str(b)])
    assert result.exit_code == 0
    assert "No differences" in result.output


def test_cli_diff_with_differences_exit_1(tmp_path):
    a = write(tmp_path, "a.env", "FOO=1\nBAR=2\n")
    b = write(tmp_path, "b.env", "FOO=1\nBAR=9\nBAZ=3\n")
    result = CliRunner().invoke(main, ["diff", str(a), str(b)])
    assert result.exit_code == 1


def test_cli_diff_redacts_by_default(tmp_path):
    a = write(tmp_path, "a.env", "SECRET=supersecret\n")
    b = write(tmp_path, "b.env", "SECRET=othersecret\n")
    result = CliRunner().invoke(main, ["diff", str(a), str(b)])
    assert "supersecret" not in result.output
    assert "othersecret" not in result.output
    assert "<set>" in result.output


def test_cli_diff_show_values(tmp_path):
    a = write(tmp_path, "a.env", "SECRET=supersecret\n")
    b = write(tmp_path, "b.env", "SECRET=othersecret\n")
    result = CliRunner().invoke(
        main, ["diff", str(a), str(b), "--show-values"]
    )
    assert "supersecret" in result.output


def test_cli_diff_json(tmp_path):
    a = write(tmp_path, "a.env", "FOO=1\n")
    b = write(tmp_path, "b.env", "FOO=2\n")
    result = CliRunner().invoke(main, ["diff", str(a), str(b), "--json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert "FOO" in data["different"]


def test_cli_check_missing_exits_1(tmp_path):
    target = write(tmp_path, ".env", "FOO=1\n")
    example = write(tmp_path, ".env.example", "FOO=\nBAR=\n")
    result = CliRunner().invoke(
        main, ["check", str(target), "--example", str(example)]
    )
    assert result.exit_code == 1
    assert "BAR" in result.output


def test_cli_check_ok(tmp_path):
    target = write(tmp_path, ".env", "FOO=1\nBAR=2\n")
    example = write(tmp_path, ".env.example", "FOO=\nBAR=\n")
    result = CliRunner().invoke(
        main, ["check", str(target), "--example", str(example)]
    )
    assert result.exit_code == 0


def test_cli_check_strict_fails_on_extra(tmp_path):
    target = write(tmp_path, ".env", "FOO=1\nEXTRA=x\n")
    example = write(tmp_path, ".env.example", "FOO=\n")
    result = CliRunner().invoke(
        main, ["check", str(target), "--example", str(example), "--strict"]
    )
    assert result.exit_code == 1


def test_cli_list_redacts_by_default(tmp_path):
    f = write(tmp_path, ".env", "FOO=secret\nBAR=\n")
    result = CliRunner().invoke(main, ["list", str(f)])
    assert result.exit_code == 0
    assert "FOO=<set>" in result.output
    assert "BAR=<empty>" in result.output
    assert "secret" not in result.output


def test_cli_list_json_show_values(tmp_path):
    f = write(tmp_path, ".env", "FOO=bar\n")
    result = CliRunner().invoke(main, ["list", str(f), "--json", "--show-values"])
    assert result.exit_code == 0
    assert json.loads(result.output) == {"FOO": "bar"}


def test_cli_parse_error_reports(tmp_path):
    f = write(tmp_path, "bad.env", "1BAD=oops\n")
    result = CliRunner().invoke(main, ["list", str(f)])
    assert result.exit_code != 0
    assert "Parse error" in result.output
