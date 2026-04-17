# envdiff

> Compare `.env` files — spot missing keys, value drift, and validate against `.env.example`. Built for humans and CI.

`envdiff` is a small, dependency-light CLI that parses `.env` files the way the shell does (quotes, escapes, `export`, comments, multiline) and tells you exactly where two env files disagree. Values are redacted by default — safe to paste into Slack or CI logs.

## Install

```sh
pip install envdiff
```

Or from source:

```sh
git clone https://github.com/farkhad/envdiff
cd envdiff
pip install -e .
```

## Usage

### Diff two files

```sh
envdiff diff .env .env.production
```

Example output:

```
        envdiff: .env vs .env.production
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ Key            ┃ Status     ┃ .env  ┃ .env.production┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ DATABASE_URL   │ different  │ <set> │ <set>          │
│ SENTRY_DSN     │ only in B  │ —     │ <set>          │
│ DEBUG          │ only in A  │ <set> │ —              │
└────────────────┴────────────┴───────┴────────────────┘
```

Reveal values with `--show-values`, or switch to machine-readable JSON with `--json`.

### Validate against an example

```sh
envdiff check .env --example .env.example
```

Exits non-zero when keys from `.env.example` are missing — perfect for a pre-deploy gate. Use `--strict` to also fail on extra keys.

### List keys

```sh
envdiff list .env
envdiff list .env --show-values --json
```

## CI usage

Add to a GitHub Actions step to catch missing env vars before a deploy:

```yaml
- name: Validate env
  run: |
    pip install envdiff
    envdiff check .env.production --example .env.example
```

`envdiff diff` and `envdiff check` both exit with code `1` when differences / missing keys are found, so they slot naturally into any CI pipeline.

## Parser notes

`envdiff`'s parser handles:

- `KEY=value` and `export KEY=value`
- Double-quoted values with escapes: `KEY="line1\nline2"`
- Single-quoted literal values: `KEY='raw\nstring'`
- Full-line and inline `#` comments (outside quotes)
- Multi-line values inside quotes
- Blank lines

## Development

```sh
make install
make test
```

## License

MIT — see [LICENSE](LICENSE).
