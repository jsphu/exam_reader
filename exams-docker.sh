#!/usr/bin/env bash

# Determine the absolute directory of the project where this script resides (resolving symlinks)
REAL_PATH="$(realpath "${BASH_SOURCE[0]}")"
PROJECT_DIR="$(cd "$(dirname "${REAL_PATH}")" && pwd)"

# Use TTY options only if stdout is connected to a terminal (important for cronjobs)
if [ -t 1 ]; then
  TTY_FLAG="-t"
else
  TTY_FLAG=""
fi

# Execute main.py inside the container with volume mounts for persistent tokens/configs
docker run --rm -i ${TTY_FLAG} \
  -v "${PROJECT_DIR}/src:/app/src" \
  -v "${PROJECT_DIR}/config.yaml:/app/config.yaml" \
  exam_reader-exam-reader \
  python main.py "$@"
