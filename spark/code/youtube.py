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
from pyspark.sql.functions import from_json
from pyspark.sql.functions import unix_timestamp, date_format
import os
import time

elastic_index = "youtubecomments"
kafkaServer = "kafkaServer:9092"
topic = "youtube"

# is there a field in the mapping that should be used to specify the ES document ID
# "es.mapping.id": "id"
# 2023-05-27T08:46:57.100Z
# se date field [2023-05-28T07:08:11.845Z] with format [yyyy-MM-dd'T'HH:mm:ss.SSSZ];
# org.elasticsearch.hadoop.rest.EsHadoopRemoteException: date_time_parse_exception: Text '2023-05-28T07:08:11.845Z' could not be parsed at index 23
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

# ESTABLISH CONNECTION TO LOGSTASH
time.sleep(int(os.getenv("SPARK_WAITING_TIME")))

es = Elasticsearch(hosts='http://10.0.100.51:9200')
# make an API call to the Elasticsearch cluster
# and have it return a response:
response = es.indices.create(
    index=elastic_index,
    body=es_mapping,
    ignore=400  # ignore 400 already exists code
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

# Training Set Schema
schema = tp.StructType([
    tp.StructField(name='id', dataType=tp.StringType(),  nullable=True),
    tp.StructField(name='subjective',
                   dataType=tp.IntegerType(),  nullable=True),
    tp.StructField(name='positive',
                   dataType=tp.IntegerType(),  nullable=True),
    tp.StructField(name='negative',
                   dataType=tp.IntegerType(),  nullable=True),
    tp.StructField(name='ironic',
                   dataType=tp.IntegerType(),  nullable=True),
    tp.StructField(name='lpositive',
                   dataType=tp.IntegerType(),  nullable=True),
    tp.StructField(name='lnegative',
                   dataType=tp.IntegerType(),  nullable=True),
    tp.StructField(name='top',       dataType=tp.IntegerType(),
                   nullable=True),
    tp.StructField(name='content',
                   dataType=tp.StringType(),   nullable=True)
])

sparkConf = SparkConf().set("es.nodes", "elasticsearch") \
    .set("es.port", "9200")
sc = SparkContext(appName="TapSentiment", conf=sparkConf)
spark = SparkSession(sc)

# Reduce the verbosity of logging messages
sc.setLogLevel("ERROR")

print("Reading training set...")
# read the dataset
training_set = spark.read.csv('../tap/spark/dataset/training_set_sentipolc16.csv',
                              schema=schema,
                              header=True,
                              sep=',')
print("Done.")

tokenizer = Tokenizer(inputCol="content", outputCol="words")
ita = StopWordsRemover.loadDefaultStopWords("italian")
stopWords = StopWordsRemover(
    inputCol='words', outputCol='filtered_words', stopWords=ita)
hashtf = HashingTF(numFeatures=2**16,
                   inputCol="filtered_words", outputCol='tf')
idf = IDF(inputCol='tf', outputCol="features", minDocFreq=5)
model = LogisticRegression(featuresCol='features',
                           labelCol='positive', maxIter=100)
pipeline = Pipeline(stages=[tokenizer, stopWords, hashtf, idf, model])

print("Training model...")
# fit the pipeline model with the training data
pipelineFit = pipeline.fit(training_set)
print("Done.")

modelSummary = pipelineFit.stages[-1].summary
print("Model Accuracy:")
print(modelSummary.accuracy)
# Streaming Query

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


# Apply the machine learning model and select only the interesting columns
df = pipelineFit.transform(df) \
    .select("created_at", "content", "author", "prediction", "video_title", "channel")

# Write the stream to elasticsearch
df.writeStream \
    .option("checkpointLocation", "/save/location") \
    .format("es") \
    .start(elastic_index) \
    .awaitTermination()
