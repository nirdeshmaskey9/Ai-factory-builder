#!/usr/bin/env python3
import argparse

def main():
    parser = argparse.ArgumentParser(description="Create a CLI that echoes input")
    parser.add_argument("--echo", help="Echo back a message", default="Hello")
    args = parser.parse_args()
    print(args.echo)

if __name__ == "__main__":
    main()
