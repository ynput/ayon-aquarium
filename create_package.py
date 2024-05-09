#!/usr/bin/env python

"""Prepares server package from addon repo to upload to server.

Requires Python 3.9. (Or at least 3.8+).

This script should be called from cloned addon repo.

It will produce 'package' subdirectory which could be pasted into server
addon directory directly (eg. into `ayon-backend/addons`).

Format of package folder:
ADDON_REPO/package/{addon name}/{addon version}

You can specify `--output_dir` in arguments to change output directory where
package will be created. Existing package directory will always be purged if
already present! This could be used to create package directly in server folder
if available.

Package contains server side files directly,
client side code zipped in `private` subfolder.
"""

import collections
import os
import platform  # ? replace with sys.platform
import re
import shutil
import subprocess
import sys
import logging
import argparse
from pathlib import Path
from typing import Iterable, Optional, Pattern
import zipfile

import package

ADDON_NAME: str = package.name
ADDON_VERSION: str = package.version

CLIENT_VERSION_CONTENT = '''# -*- coding: utf-8 -*-
"""Package declaring {} addon version."""
__version__ = "{}"
'''

CURRENT_DIR: Path = Path(__file__).parent
SERVER_DIR: Path = CURRENT_DIR / "server"
CLIENT_DIR: Path = CURRENT_DIR / "client" / package.client_dir

# COMMON_DIR: Path = CLIENT_DIR / ADDON_CLIENT_DIR / "common"

# Patterns of directories to be skipped for server part of addon
IGNORE_DIR_PATTERNS: list[Pattern] = [
    re.compile(pattern)
    for pattern in {
        # Skip directories starting with '.'
        r"^\.",
        # Skip any pycache folders
        "^__pycache__$",
    }
]

# Patterns of files to be skipped for server part of addon
IGNORE_FILE_PATTERNS: list[Pattern] = [
    re.compile(pattern)
    for pattern in {
        # Skip files starting with '.'
        # NOTE this could be an issue in some cases
        r"^\.",
        # Skip '.pyc' files
        r"\.pyc$",
    }
]

log = logging.getLogger(__name__)


class ZipFileLongPaths(zipfile.ZipFile):
    """Allows longer paths in zip files.

    Regular DOS paths are limited to MAX_PATH (260) characters, including
    the string's terminating NUL character.
    That limit can be exceeded by using an extended-length path that
    starts with the '\\?\' prefix.
    """

    _is_windows = platform.system().lower() == "windows"

    def _extract_member(self, member, tpath, pwd):
        if self._is_windows:
            tpath = os.path.abspath(tpath)
            if tpath.startswith("\\\\"):
                tpath = "\\\\?\\UNC\\" + tpath[2:]
            else:
                tpath = "\\\\?\\" + tpath

        return super(ZipFileLongPaths, self)._extract_member(member, tpath, pwd)


def safe_copy_file(src: Path, dst: Path):
    log.debug(f"Copying {src} to {dst}")
    if src.is_file():
        if not dst.parent.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _value_match_regexes(value: str, regexes: Iterable[Pattern]) -> bool:
    return any(regex.search(value) for regex in regexes)


def update_client_version():
    version_file = CLIENT_DIR / "version.py"
    log.debug(f"{version_file = }")
    if not version_file.exists():
        raise RuntimeError(f"Version file '{version_file}' does not exist!")
    log.debug(f"Updating client version in {version_file}")

    with version_file.open("w") as f:
        f.write(CLIENT_VERSION_CONTENT.format(ADDON_NAME, ADDON_VERSION))


def get_files_to_copy(search_path: Path):
    result = set()
    for file in search_path.rglob("*"):  # could even filter here
        if file.is_file():
            if _value_match_regexes(file.name, IGNORE_FILE_PATTERNS):
                continue
            if file.name == f"{ADDON_NAME}-{ADDON_VERSION}.zip":
                continue
            result.add(file)

    return result


def copy_package_file(target: Path):
    log.debug("Copying package file")
    safe_copy_file(CURRENT_DIR / "package.py", target / "package.py")


def _build_frontend():
    frontend_dir: Path = CURRENT_DIR / "server" / "frontend"
    if not frontend_dir.exists():
        log.info("Frontend directory was not found. Skipping")
        return

    # frontend_dist_dir: str = frontend_dir / "dist"

    if Path(frontend_dir, "package.json").exists():
        # assume that frontend is a node project and we need to build it
        executable = shutil.which("npm") or shutil.which("yarn")

        if executable is None:
            raise RuntimeError("npm and yarn executable was not found.")

        install_command = [executable, "install"]
        build_command = [executable, "build"]

        if "npm" in executable:
            build_command.insert(1, "run")
            install_command[1] = "ci"
        if "yarn" in executable:
            subprocess.run(
                [executable, "import"], cwd=frontend_dir
            )  # Convert package-lock.json to yarn.lock

        subprocess.run(install_command, cwd=frontend_dir)
        subprocess.run(build_command, cwd=frontend_dir)


def copy_frontend_content(target: Path):
    target = target / "frontend" / "dist"
    log.debug(f"Copying frontend code --> {target}")

    frontend_dist_dir: Path = CURRENT_DIR / "server" / "frontend" / "dist"
    _build_frontend()

    for file in get_files_to_copy(frontend_dist_dir):
        # C:\Users\Tony.Dorfmeister\dev\new-gitea\ayon\ayon-aquarium\server\frontend\dist\assets\index-91b6b809.css
        # C:\Users\Tony.Dorfmeister\dev\new-gitea\ayon\ayon-aquarium\build\aquarium\0.0.4-dev.1\frontend\dist\assets\index-91b6b809.css
        safe_copy_file(file, target / Path(*file.relative_to(CURRENT_DIR).parts[3:]))


def copy_client_content(target: Path):
    # log.debug(f"Copying client code --> {target}")

    if target.is_dir():
        shutil.rmtree(target)

    # recreate target folder
    if target.exists():
        raise RuntimeError(f"Failed to remove target folder '{target}'")
    target.mkdir(parents=True, exist_ok=True)

    update_client_version()

    for file in get_files_to_copy(CLIENT_DIR):
        safe_copy_file(file, file.relative_to(CURRENT_DIR / "client"))


def zip_client_content(target: Path):
    zip_filepath: Path = target / "private" / "client.zip"
    if not zip_filepath.parent.exists():
        zip_filepath.parent.mkdir(parents=True, exist_ok=True)
    with ZipFileLongPaths(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add client code content to zip
        for path in get_files_to_copy(CLIENT_DIR):
            zipf.write(path, path.relative_to(CURRENT_DIR / "client"))

    log.info("Client zip created")

    pyproject_path = CURRENT_DIR / "client" / "pyproject.toml"
    if os.path.exists(pyproject_path):
        shutil.copy(pyproject_path, target / "private")


def copy_server_content(target: Path):
    # ? do i need the frontend code here
    target = target / "server"
    log.debug(f"Copying server code --> {target}")

    for file in get_files_to_copy(SERVER_DIR):
        safe_copy_file(file, target / file.relative_to(SERVER_DIR))


def create_server_package(target: Path):
    """Create server package zip file.

    The zip file can be installed to a server using UI or rest api endpoints.

    Args:
        output_dir (str): Directory path to output zip file.
        addon_output_dir (str): Directory path to addon output directory.
        log (logging.Logger): Logger object.
    """

    log.info("Creating server package")
    output_path = target / f"{ADDON_NAME}-{ADDON_VERSION}.zip"

    with ZipFileLongPaths(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Move addon content to zip into 'addon' directory
        addon_output_dir_offset = len(CURRENT_DIR.parts) + 1
        for root, _, filenames in os.walk(CURRENT_DIR):
            if not filenames:
                continue

            dst_root = None
            if root != CURRENT_DIR:
                dst_root = root[addon_output_dir_offset:]
            for filename in filenames:
                src_path = os.path.join(root, filename)
                dst_path = filename
                if dst_root:
                    dst_path = os.path.join(dst_root, dst_path)
                zipf.write(src_path, dst_path)

    log.info(f"Output package can be found: {output_path}")


def main(
    target_dir: Optional[str],
    skip_zip: Optional[bool] = False,
    keep_sources: Optional[bool] = False,
    only_client: Optional[bool] = False,
):
    # validate target_root
    target_root: Path
    if not target_dir:
        target_root = CURRENT_DIR / "build"
    if not isinstance(target_root, Path):
        target_root = Path(target_dir)
    if not target_root:
        raise RuntimeError(
            "Output directory must be defined" " for client only preparation."
        )

    # copies client folder
    if only_client:
        log.info("Creating client folder")
        copy_client_content(target_root)
        log.info("Client folder created")
        return

    # build version addon root
    target_package_root: Path = target_root / ADDON_NAME / ADDON_VERSION
    if target_package_root.exists():
        log.info(f"Purging {target_package_root}")
        shutil.rmtree(target_package_root)

    log.info(f"Preparing package for {ADDON_NAME}-{ADDON_VERSION}")

    if not target_package_root.exists():
        target_package_root.mkdir(parents=True, exist_ok=True)

    try:
        # copy package file
        copy_package_file(target_package_root)
        # copy server content
        copy_server_content(target_package_root)
        # copy frontend content
        copy_frontend_content(target_package_root)
        # zip client code
        zip_client_content(target_package_root)
    except Exception as e:
        log.error(f"Failed to prepare package: {e}")
        raise
    finally:
        pass
        # # cleanup after build
        # target_package: Path = target_root / ADDON_NAME / ADDON_VERSION
        # if target_root.is_dir():
        #     log.info(f"Purging {target_package}")
        #     shutil.rmtree(target_package)

    if not skip_zip:
        # create server package
        create_server_package(target_package_root)
        # pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-zip",
        dest="skip_zip",
        action="store_true",
        help=(
            "Skip zipping server package and create only" " server folder structure."
        ),
    )
    parser.add_argument(
        "--keep-sources",
        dest="keep_sources",
        action="store_true",
        help=("Keep folder structure when server package is created."),
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_dir",
        default=None,
        help=(
            "Directory path where package will be created"
            " (Will be purged if already exists!)"
        ),
    )
    parser.add_argument(
        "--only-client",
        dest="only_client",
        action="store_true",
        help=(
            "Extract only client code. This is useful for development."
            " Requires '-o', '--output' argument to be filled."
        ),
    )
    parser.add_argument(
        "--debug", dest="debug", action="store_true", help="Debug log messages."
    )

    args = parser.parse_args(sys.argv[1:])
    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)
    main(args.output_dir, args.skip_zip, args.keep_sources, args.only_client)
