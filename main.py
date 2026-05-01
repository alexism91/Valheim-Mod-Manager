#!/usr/bin/env python3
import sys
import logging
from vmm.fonts import load_bundled_fonts
from vmm.app import ValheimModManagerApp

# Configuration du logging global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

def main():
    load_bundled_fonts()
    app = ValheimModManagerApp()
    sys.exit(app.run(sys.argv))

if __name__ == '__main__':
    main()
