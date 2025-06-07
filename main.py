import json
import os
import random
import yt_dlp
import tweepy
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self, source_file=None):
        self.source_file = source_file or "db.json"
        self.videos = []
        self.load_videos()

    def load_videos(self):
        if not os.path.exists(self.source_file):
            return
        with open(self.source_file, "r") as f:
            self.videos = json.load(f)

    def save_videos(self):
        with open(self.source_file, "w") as f:
            json.dump(self.videos, f)

    def add_video(self, video):
        self.videos.append(video)
        self.save_videos()

    def update_video(self, video_id, post_id):
        self.videos[video_id]["post_id"] = post_id
        self.save_videos()

    def get_unposted_videos(self):
        return [video for video in self.videos if not video.get("post_id")]

class XPoster:
    def __init__(self):
        # Twitter API credentials
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        # Initialize Twitter API v2
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
        )

        # Initialize Twitter API v1
        auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

    def post(self, video_path, successful_person):
        try:
            media = self.api.media_upload(video_path, chunked=True, media_category="tweet_video")

            # TODO: get a more interesting text from analyzing the video
            text = f"Motivational stuff from {successful_person.title()}"
            # post the media
            post = self.client.create_tweet(text=text, media_ids=[media.media_id])
            return post.data["id"]
        except Exception as e:
            print(f"Error posting video: {e}")
            raise e
            return None

class Video:
    def __init__(self, successful_person, db, num_videos=1, output_dir="videos"):
        self.successful_person = successful_person
        self.num_videos = num_videos
        self.db = db
        self.output_dir = output_dir

        # create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def get_videos(self):
        query = f"motivational interview or speech or talk + {self.successful_person}"

        # Specify exact output path
        ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'format': 'best[ext=mp4]',  # Ensure mp4 format
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch{self.num_videos}:{query}", download=False)

            for entry in result["entries"]:
                if entry["id"] in self.db.videos:
                    continue

                # download the video
                file_path = os.path.join(self.output_dir, f"{entry['title']}.mp4")
                ydl.download([entry["webpage_url"]])
                # add filepath to entry
                entry["filepath"] = file_path
                self.db.add_video({entry["id"]: entry})
                # break after downloading the first video
                return entry["id"]


def get_successful_person():
    with open("successful.txt", "r") as f:
        lines = f.read().splitlines()

    # remove comments
    lines = [line for line in lines if not line.startswith("#")]
    # return one random line
    return random.choice(lines)

if __name__ == "__main__":
    # get successful name
    successful_person = get_successful_person()
    db = Database()
    video = Video(successful_person, db)
    # get unposted videos
    unposted_videos = db.get_unposted_videos()

    if unposted_videos:
        print("Found unposted videos!!")
        video_id, video_data = list(unposted_videos[0].items())[0]
        file_path = video_data["filepath"]
        print(f"Posting video {video_id} with title {video_data['title']}")
    else:
        print("No unposted videos found, getting new ones")
        video_id = video.get_videos()
        video_data = db.videos[video_id]
        file_path = video_data["filepath"]

    xposter = XPoster()
    post_id = xposter.post(file_path, successful_person)
    # update the video with the post_id
    db.update_video(video_id, post_id)
