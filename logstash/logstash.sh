#!/usr/bin/env bash
# Stop
docker stop logstash

# Remove previuos container 
docker container rm logstash

docker build . -t yt:logstash
docker run --network tap  --ip 10.0.100.30 -p 6000:6000 --name logstash --rm -it -v $PWD/pipeline/youtube.conf:/usr/share/logstash/pipeline/logstash.conf yt:logstash