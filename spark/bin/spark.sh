bash ./sparkSubmitPythonV.sh youtube.py "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.elasticsearch:elasticsearch-spark-30_2.12:8.7.1"


docker run -e SPARK_ACTION=spark-submit-python -v sparklibs:/root/.ivy2 -p 4040:4040 --network tap --name sparkSubmit -it yt:spark youtube.py "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.elasticsearch:elasticsearch-spark-30_2.12:8.7.1"