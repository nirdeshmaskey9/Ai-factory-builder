# reverse_cli — CLI

## Usage

```bash
python reverse_cli.py --echo "Hello"
```

## Options

- `--echo` Echo back the provided message (default: "Hello")

## Development

- The CLI is a simple `argparse` program. Extend `main()` to add commands.
- Artifacts live under `builds/<build_id>/outputs/reverse_cli/`.