#!/bin/bash
# wait 20 seconds for kafka to start
sleep 20
#creat topic
# kafka-topics.sh --create --topic yt --bootstrap-server kafka:9092
kafka-topics.sh --create --bootstrap-server 10.0.100.23:9092 --replication-factor 1 --partitions 1 --topic youtube
