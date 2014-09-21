#!/usr/bin/env python
import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webgcal.settings")

    from swampdragon.swampdragon_server import run_server

    run_server()
