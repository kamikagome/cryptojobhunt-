#!/usr/bin/env python3
"""Initialize the crypto jobs database."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.connection import init_db

if __name__ == "__main__":
    init_db()
    print("Database setup complete!")
