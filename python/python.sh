#!/usr/bin/env bash
# Stop
docker stop youtubePython

# Remove previuos container 
docker container rm youtubePython

docker build . -t yt:python
docker run --rm -it --network tap --name youtubePython -e PYTHON_APP=streaming-youtube.py yt:python /bin/bash