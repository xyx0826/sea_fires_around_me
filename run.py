# run.py: reads configuration and starts the watcher.

import json
import os
import time

from realtime import RealTime


def main():
    # Check config file
    if not os.path.isfile("config.json"):
        print(
            "Error: could not find config.json."
            "Make sure you have written your API key and origin into "
            "config.json.sample and renamed it to config.json."
        )
        return

    cfg = None
    with open("config.json", "r") as f:
        cfg = json.load(f)

    rt = RealTime(
        cfg["origin_lat"], cfg["origin_lon"], cfg["mapquest_api_key"])
    while True:
        rt.update()
        time.sleep(20)


if __name__ == "__main__":
    main()
