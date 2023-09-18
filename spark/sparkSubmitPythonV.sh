#!/usr/bin/env bash
# Stop
docker stop sparkSubmit

# Remove previuos container 
docker container rm sparkSubmit

docker build . --tag yt:spark

docker run -e SPARK_ACTION=spark-submit-python -v sparklibs:/root/.ivy2 -p 4040:4040 --network tap --name sparkSubmit -it yt:spark $1 $2