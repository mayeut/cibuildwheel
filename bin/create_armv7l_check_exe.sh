#!/bin/sh

set -eux

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
RESOURCES_DIR="${SCRIPT_DIR}/../cibuildwheel/resources"

docker run --platform linux/arm/v7 -i --rm -v "${RESOURCES_DIR}:/resources" alpine:3.21 << "EOFD"
apk add build-base
gcc -s -Os -static -x c -o/resources/linux_armv7l_check - << "EOF"
#include <stdio.h>

int main(int argc, char* argv[]) {
  puts("armv7l");
  return 0;
}
EOF
EOFD
