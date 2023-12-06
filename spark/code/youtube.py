from pyspark import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
from pyspark import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql.functions import from_json
import pyspark.sql.types as tp
from pyspark.ml import Pipeline
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import HashingTF, IDF, Tokenizer
from pyspark.ml.classification import LogisticRegression
from pyspark import SparkContext
from pyspark.sql import SparkSession
from elasticsearch import Elasticsearch
from pyspark.sql import functions as F
from pyspark.sql.functions import udf
from pyspark.sql.functions import from_json
from pyspark.sql.functions import unix_timestamp, date_format
from feel_it import SentimentClassifier
import os
import time


elastic_index = "youtubecomments"
kafkaServer = "kafkaServer:9092"
topic = "youtube"

sentiment_classifier = SentimentClassifier()

es_mapping = {
    "mappings": {
        "properties":
            {
                "created_at": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss"},
                "content": {"type": "text", "fielddata": "true"},
                "author": {"type": "keyword"},
                "video_title": {"type": "keyword"},
                "channel": {"type": "keyword"},
            }
    }
}

time.sleep(int(os.getenv("SPARK_WAITING_TIME")))

es = Elasticsearch(hosts='http://10.0.100.51:9200')
response = es.indices.create(
    index=elastic_index,
    body=es_mapping,
    ignore=400 
)

if 'acknowledged' in response:
    if response['acknowledged'] == True:
        print("INDEX MAPPING SUCCESS FOR INDEX:", response['index'])

# Define Training Set Structure
ytComment = tp.StructType([
    tp.StructField(name='@version', dataType=tp.StringType(),  nullable=True),
    tp.StructField(name='created_at',
                   dataType=tp.StringType(),  nullable=True),
    tp.StructField(name='content', dataType=tp.StringType(),  nullable=True),
    tp.StructField(name='author', dataType=tp.StringType(),  nullable=True),
    tp.StructField(name='video_title', dataType=tp.StringType(),  nullable=True),
    tp.StructField(name='channel', dataType=tp.StringType(),  nullable=True)
])

def sentiment(text):
    arr = [text]
    resp = sentiment_classifier.predict(arr)
    return resp[0]

def createSparkSession():
    sparkConf = SparkConf().set("es.nodes", "elasticsearch") \
        .set("es.port", "9200")
    sc = SparkContext(appName="TapSentiment", conf=sparkConf)
    sc.setLogLevel("ERROR")
    return SparkSession(sc)

spark = createSparkSession()

print("Reading stream from kafka...")
# Read the stream from kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", topic) \
    .load()

# Cast the message received from kafka with the provided schema
df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", ytComment).alias("data")) \
    .select("data.*")

sentiment_udf = udf(sentiment,tp.StringType())
df = df.withColumn("prediction", sentiment_udf("content"))

df = df.select("created_at", "content", "author", "prediction", "video_title", "channel")

df.printSchema()

df.writeStream \
    .option("checkpointLocation", "/save/location") \
    .format("es") \
    .start(elastic_index) \
    .awaitTermination()
