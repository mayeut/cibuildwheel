#!/usr/bin/env python3

import configparser
from dataclasses import dataclass
from pathlib import Path

import requests
from packaging.version import Version

DIR = Path(__file__).parent.resolve()
RESOURCES = DIR.parent / "cibuildwheel/resources"


@dataclass(frozen=True)
class Image:
    manylinux_version: str
    platforms: list[str]
    image_name: str
    tag: str | None  # Set this to pin the image


class PyPAImageEOL(Image):
    def __init__(self, manylinux_version: str, platform: str, tag: str):
        platform_no_pypy = platform.removeprefix("pypy_")
        image_name = f"quay.io/pypa/{manylinux_version}_{platform_no_pypy}"
        super().__init__(manylinux_version, [platform], image_name, tag)


class PyPAImage(Image):
    def __init__(self, manylinux_version: str, platforms: list[str], tag: str | None):
        image_name = f"quay.io/pypa/{manylinux_version}"
        super().__init__(manylinux_version, platforms, image_name, tag)


images = [
    # manylinux1 images, EOL -> use tag
    PyPAImageEOL("manylinux1", "x86_64", "2024-04-29-76807b8"),
    PyPAImageEOL("manylinux1", "i686", "2024-04-29-76807b8"),
    # manylinux2010 images, EOL -> use tag
    PyPAImageEOL("manylinux2010", "x86_64", "2022-08-05-4535177"),
    PyPAImageEOL("manylinux2010", "i686", "2022-08-05-4535177"),
    PyPAImageEOL("manylinux2010", "pypy_x86_64", "2022-08-05-4535177"),
    PyPAImageEOL("manylinux2010", "pypy_i686", "2022-08-05-4535177"),
    # manylinux2014 images
    PyPAImage(
        "manylinux2014",
        [
            "x86_64",
            "i686",
            "aarch64",
            "ppc64le",
            "s390x",
            "pypy_x86_64",
            "pypy_i686",
            "pypy_aarch64",
        ],
        None,
    ),
    # manylinux_2_24 images, EOL -> use tag
    PyPAImageEOL("manylinux_2_24", "x86_64", "2022-12-26-0d38463"),
    PyPAImageEOL("manylinux_2_24", "i686", "2022-12-26-0d38463"),
    PyPAImageEOL("manylinux_2_24", "aarch64", "2022-12-26-0d38463"),
    PyPAImageEOL("manylinux_2_24", "ppc64le", "2022-12-26-0d38463"),
    PyPAImageEOL("manylinux_2_24", "s390x", "2022-12-26-0d38463"),
    PyPAImageEOL("manylinux_2_24", "pypy_x86_64", "2022-12-26-0d38463"),
    PyPAImageEOL("manylinux_2_24", "pypy_i686", "2022-12-26-0d38463"),
    PyPAImageEOL("manylinux_2_24", "pypy_aarch64", "2022-12-26-0d38463"),
    # manylinux_2_28 images
    PyPAImage(
        "manylinux_2_28",
        ["x86_64", "aarch64", "ppc64le", "s390x", "pypy_x86_64", "pypy_aarch64"],
        None,
    ),
    # manylinux_2_31 images
    PyPAImage("manylinux_2_31", ["armv7l"], None),
    # manylinux_2_34 images
    PyPAImage(
        "manylinux_2_34",
        ["x86_64", "aarch64", "ppc64le", "s390x", "pypy_x86_64", "pypy_aarch64"],
        None,
    ),
    # musllinux_1_1 images, EOL -> use tag
    PyPAImageEOL("musllinux_1_1", "x86_64", "2024.10.26-1"),
    PyPAImageEOL("musllinux_1_1", "i686", "2024.10.26-1"),
    PyPAImageEOL("musllinux_1_1", "aarch64", "2024.10.26-1"),
    PyPAImageEOL("musllinux_1_1", "ppc64le", "2024.10.26-1"),
    PyPAImageEOL("musllinux_1_1", "s390x", "2024.10.26-1"),
    # musllinux_1_2 images
    PyPAImage("musllinux_1_2", ["x86_64", "aarch64", "ppc64le", "s390x", "armv7l"], None),
]

config = configparser.ConfigParser()

for image in images:
    # get the tag name whose digest matches 'latest'
    if image.tag is not None:
        # image has been pinned, do not update
        tag_name = image.tag
    elif image.image_name.startswith("quay.io/"):
        _, _, repository_name = image.image_name.partition("/")
        response = requests.get(
            f"https://quay.io/api/v1/repository/{repository_name}?includeTags=true"
        )
        response.raise_for_status()
        repo_info = response.json()
        tags_dict = repo_info["tags"]

        latest_tag = tags_dict.pop("latest")
        # find the tag whose manifest matches 'latest'
        tag_name = next(
            name
            for (name, info) in tags_dict.items()
            if info["manifest_digest"] == latest_tag["manifest_digest"]
        )
    elif image.image_name.startswith("ghcr.io/"):
        repository = image.image_name[8:]
        response = requests.get(
            "https://ghcr.io/token", params={"scope": f"repository:{repository}:pull"}
        )
        response.raise_for_status()
        token = response.json()["token"]
        response = requests.get(
            f"https://ghcr.io/v2/{repository}/tags/list",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        ghcr_tags = [(Version(tag), tag) for tag in response.json()["tags"] if tag != "latest"]
        ghcr_tags.sort(reverse=True)
        tag_name = ghcr_tags[0][1]
    else:
        response = requests.get(f"https://hub.docker.com/v2/repositories/{image.image_name}/tags")
        response.raise_for_status()
        tags = response.json()["results"]

        latest_tag = next(tag for tag in tags if tag["name"] == "latest")
        # i don't know what it would mean to have multiple images per tag
        assert len(latest_tag["images"]) == 1
        digest = latest_tag["images"][0]["digest"]

        pinned_tag = next(
            tag for tag in tags if tag != latest_tag and tag["images"][0]["digest"] == digest
        )
        tag_name = pinned_tag["name"]

    for platform in image.platforms:
        if not config.has_section(platform):
            config[platform] = {}
        config[platform][image.manylinux_version] = f"{image.image_name}:{tag_name}"

with open(RESOURCES / "pinned_docker_images.cfg", "w") as f:
    config.write(f)
