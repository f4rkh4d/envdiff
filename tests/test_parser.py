import pytest

from envdiff.parser import ParseError, parse_text


def test_simple_kv():
    assert parse_text("FOO=bar") == {"FOO": "bar"}


def test_export_prefix():
    assert parse_text("export FOO=bar\nexport\tBAZ=qux") == {"FOO": "bar", "BAZ": "qux"}


def test_double_quoted_with_escapes():
    got = parse_text(r'''FOO="a\nb\tc\"d"''')
    assert got == {"FOO": "a\nb\tc\"d"}


def test_single_quoted_is_literal():
    got = parse_text(r"""FOO='a\nb'""")
    assert got == {"FOO": r"a\nb"}


def test_comments_and_blank_lines():
    text = """
# a comment
FOO=bar

# another
BAZ=qux
"""
    assert parse_text(text) == {"FOO": "bar", "BAZ": "qux"}


def test_inline_comment_unquoted():
    assert parse_text("FOO=bar # trailing") == {"FOO": "bar"}


def test_inline_hash_inside_quotes_preserved():
    assert parse_text('FOO="a#b"') == {"FOO": "a#b"}


def test_multiline_double_quoted_value():
    text = 'FOO="line1\nline2"\nBAR=baz'
    assert parse_text(text) == {"FOO": "line1\nline2", "BAR": "baz"}


def test_empty_value():
    assert parse_text("FOO=") == {"FOO": ""}


def test_invalid_key_raises():
    with pytest.raises(ParseError):
        parse_text("1BAD=value")


def test_missing_equals_raises():
    with pytest.raises(ParseError):
        parse_text("NOEQUALS")


def test_unterminated_quote_raises():
    with pytest.raises(ParseError):
        parse_text('FOO="unterminated')


def test_later_value_wins():
    assert parse_text("FOO=a\nFOO=b") == {"FOO": "b"}


def test_whitespace_around_key():
    assert parse_text("  FOO = bar  ") == {"FOO": "bar"}
