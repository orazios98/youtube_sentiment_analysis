# Elasticsearch

Elasticsearch is a distributed, RESTful search and analytics engine capable of solving a growing number of use cases. As the heart of the Elastic Stack, it centrally stores your data so you can discover the expected and uncover the unexpected.

## Usage

After running docker-compose, Elasticsearch is available at http://localhost:9200

To view the data, you can use the following command:

```shell
$ curl -X GET "localhost:9200/youtubecomments/_search?pretty"
```
