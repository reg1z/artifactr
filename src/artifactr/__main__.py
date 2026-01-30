"""Entry point for running Artifactr as a module.

Allows running via: python -m artifactr
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
