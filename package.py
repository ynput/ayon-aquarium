name = "aquarium"
title = "Aquarium"
version = "0.0.4-dev.1"
client_dir = "ayon_aquarium"

services = {
    "leecher": {"image": f"ynput/ayon-aquarium-leecher:{version}"},
    "processor": {"image": f"ynput/ayon-aquarium-processor:{version}"},
}

plugin_for = ["ayon_server"]
