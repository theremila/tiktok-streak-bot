#!/usr/bin/env python3
import os
import sys

# Ensure src/ is on python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tiktok_bot.__main__ import main

if __name__ == "__main__":
    main()
