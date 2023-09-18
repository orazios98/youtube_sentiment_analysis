from youtube_api import YouTubeDataAPI
import socket
import json
import time
import os
import datetime

HOST=os.getenv("LOGSTASH_IP")
PORT=os.getenv("LOGSTASH_PORT")
VIDEO_URL=os.getenv("VIDEO_URL")
API_KEY=os.getenv("API_KEY")
SEND_OLD_COMMENT=os.getenv("SEND_OLD_COMMENTS")

error=True
while(error):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, int(PORT)))
        
        sock.close()
        error = False
    except:
        print("ERROR:")
        print('Connection error. There will be a new attempt in 5 seconds\n')
        time.sleep(5)

s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, int(PORT)))
print("STREAM CONNESSO")

api_key = API_KEY
print("APIKEY: ",api_key)
yt = YouTubeDataAPI(api_key)

def formatComment(comment):
    timestamp_not_formatted = comment['comment_publish_date']
    timestamp = datetime.datetime.fromtimestamp(timestamp_not_formatted).strftime('%Y-%m-%d %H:%M:%S')
    return {
        'content': comment['text'],
        'author': comment['commenter_channel_display_name'],
        'created_at': timestamp,
    }

def get_comments(last_item):
    comments = yt.get_video_comments(VIDEO_URL, order_by_time=True)
        
    if not comments:
        print("no comments")
        return None
    
    last_comment = comments[0]
    last_comment_id = last_comment['comment_id']
    
    if last_item is None:
        if SEND_OLD_COMMENT:
            print("waiting to send old comment")
            time.sleep(90)
            for item in comments:
                log_message = formatComment(item)
                s.sendall(json.dumps(log_message).encode('utf-8'))
                s.send(bytes('\n','utf-8'))
        return last_comment_id

    if last_item != last_comment_id:
        print("new comment")
        for item in comments:
            if(item['comment_id'] == last_item):
                break
            log_message = formatComment(item)
            s.sendall(json.dumps(log_message).encode('utf-8'))
            s.send(bytes('\n','utf-8'))
        return last_comment_id
    
    if last_item == last_comment_id:
        print("no new comment")
        return last_comment_id

last_item=None 
while True:
    last_item=get_comments(last_item)    
    print("wait",flush=True)
    time.sleep(30)