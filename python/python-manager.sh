#!/bin/bash
[[ -z "${PYTHON_APP}" ]] && { echo "PYTHON_APP required"; exit 1; }

echo "Running python ${PYTHON_APP} (Python Dir:${PYTHON_DIR})"
python3 ${PYTHON_APP}
