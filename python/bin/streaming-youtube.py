from youtube_api import YouTubeDataAPI
import socket
import json
import time
import os
import datetime
import requests

HOST=os.getenv("LOGSTASH_IP")
PORT=os.getenv("LOGSTASH_PORT")
CHANNEL_URL=os.getenv("CHANNEL_URL")
MAX_VIDEO_RESULTS=os.getenv("MAX_VIDEO_RESULTS")
API_KEY=os.getenv("API_KEY")
SEND_OLD_COMMENT=os.getenv("SEND_OLD_COMMENTS")
WAITING_TIME=os.getenv("WAITING_TIME")
CHANNEL_TITLE = ""
DATE = os.getenv("DATE")

videos_comments_dict = {}
videos_title_dict = {}

yt = YouTubeDataAPI(API_KEY)

req = "https://www.googleapis.com/youtube/v3/search?key="+API_KEY+"&channelId="+CHANNEL_URL+"&part=snippet,id&order=date&maxResults="+MAX_VIDEO_RESULTS

def formatComment(comment, videoId):
    timestamp_not_formatted = comment['comment_publish_date']
    timestamp = datetime.datetime.fromtimestamp(timestamp_not_formatted).strftime('%Y-%m-%d %H:%M:%S')
    return {
        'content': comment['text'],
        'video_id': comment['video_id'],
        'video_title': videos_title_dict[videoId],
        'author': comment['commenter_channel_display_name'],
        'created_at': timestamp,
        'channel': CHANNEL_TITLE
    }

def send_comment(comment):
    s.sendall(json.dumps(comment).encode('utf-8'))
    s.send(bytes('\n','utf-8'))

    
def get_comments(video_id):
    try:
        comments = yt.get_video_comments(video_id, order_by_time=True, max_results=20)
    except Exception as e:
        print(f"An error occurred: {e}")
        comments = None
        
    if not comments:
        print("no comments")
        videos_comments_dict[video_id] = None
        return
    
    last_comment_id = comments[0]['comment_id']
    last_item = videos_comments_dict[video_id]
    
    if last_item is None:
        print("first time. Send old comment: ",SEND_OLD_COMMENT)
        if SEND_OLD_COMMENT:
            print("waiting to send old comment")
            time.sleep(120)
            
            print("DATE", DATE)
            # filter comments published after date
            comments = [comment for comment in comments if comment['comment_publish_date'] > time.mktime(time.strptime(DATE, "%d/%m/%Y %H:%M:%S"))]
            for item in comments:
                log_message = formatComment(item, video_id)
                send_comment(log_message)
        videos_comments_dict[video_id] = last_comment_id
        return
    
    if last_item != last_comment_id:
        print("new comment")
        for item in comments:
            if(item['comment_id'] == last_item):
                break
            log_message = formatComment(item, video_id)
            send_comment(log_message)
        videos_comments_dict[video_id] = last_comment_id
        return
    
    if last_item == last_comment_id:
        print("no new comment")
        videos_comments_dict[video_id] = last_comment_id
        return

def get_video_urls():
    items = []
    try:
        resp = requests.get(req)
        resp.raise_for_status()
        json_resp = resp.json()
        global CHANNEL_TITLE
        CHANNEL_TITLE = json_resp['items'][0]['snippet']['channelTitle']
        items = json_resp['items']
    except Exception as e:
        print(f"Error during request to get videos: {e}")

    videos_url = []
    
    for item in items:
        if(item['id']['kind'] != 'youtube#video'):
            continue
        title = item['snippet']['title']
        url = item['id']['videoId']
        video = {
            'id': url,
            'title': title
        }
        videos_url.append(video)
    return videos_url

def init_videos_comments_dict():
    videos = get_video_urls()
    for video in videos:
        videos_comments_dict[video['id']] = None
        videos_title_dict[video['id']] = video['title']
        
def add_videos_to_dict(videos):
    for video in videos:
        if video['id'] not in videos_comments_dict:
            videos_comments_dict[video['id']] = None
            videos_title_dict[video['id']] = video['title']


def checkVideoAndComment():
    videos = get_video_urls()
    add_videos_to_dict(videos)
    for video in videos:
        get_comments(video['id'])

def checkComments():
    for video in videos_comments_dict:
        get_comments(video)

if __name__ == "__main__":
    print("WAIT",WAITING_TIME)
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
    
    init_videos_comments_dict()
    index = 0
    while True:
        if index == 0:
            print("checkVideoAndComment",flush=True)
            checkVideoAndComment()
        else:
            print("checkComments",flush=True)
            checkComments()

        index = (index + 1) % 15
            
        print("wait",flush=True)
        minutes = int(WAITING_TIME) * 60
        time.sleep(minutes)      