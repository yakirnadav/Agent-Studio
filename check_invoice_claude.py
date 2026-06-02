#!/usr/bin/env python3
"""Entry point for the Claude-integrated invoice checker CLI."""
import sys
from invoice_checker.claude_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
