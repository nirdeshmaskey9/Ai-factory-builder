# app — CLI

## Usage

```bash
python app.py --echo "Hello"
```

## Options

- `--echo` Echo back the provided message (default: "Hello")

## Development

- The CLI is a simple `argparse` program. Extend `main()` to add commands.
- Artifacts live under `builds/<build_id>/outputs/app/`.