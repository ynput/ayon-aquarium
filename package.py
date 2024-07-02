name = "aquarium"
title = "Aquarium"
version = "0.0.4"

client_dir = "ayon_aquarium"

# Match Services names created by manage.ps1 or makefile
services = {
        "leecher": {"image": f"ghcr.io/fatfish-lab/ayon-aquarium-leecher:{version}"},
        "processor": {"image": f"ghcr.io/fatfish-lab/ayon-aquarium-processor:{version}"}
    }

plugin_for = ["ayon_server"]