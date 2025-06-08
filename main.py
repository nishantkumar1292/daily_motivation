import json
import os
import random
import yt_dlp
from dotenv import load_dotenv
from poster import XPoster

load_dotenv()

class Database:
    def __init__(self, source_file=None):
        self.source_file = source_file or "db.json"
        self.videos = {}
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
        self.videos[video["id"]] = video
        self.save_videos()

    def update_video(self, video_id, post_id):
        self.videos[video_id]["post_id"] = post_id
        self.save_videos()

    def get_unposted_videos(self):
        return [(video_id, video) for video_id, video in self.videos.items() if not video.get("post_id")]

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

                # download the video and get the actual file path
                download_result = ydl.extract_info(entry["webpage_url"], download=True)
                actual_filename = ydl.prepare_filename(download_result)

                # add filepath to entry
                entry["filepath"] = actual_filename
                # add successful person to entry
                entry["successful_person"] = self.successful_person
                self.db.add_video(entry)
                # break after downloading the first video
                return entry["id"]


def get_successful_person():
    with open("successful.txt", "r") as f:
        lines = f.read().splitlines()

    # remove comments and empty lines
    lines = [line for line in lines if not line.startswith("#") and line.strip()]
    # return one random line
    return random.choice(lines)

if __name__ == "__main__":
    db = Database()
    # get unposted videos
    unposted_videos = db.get_unposted_videos()

    if unposted_videos:
        print("Found unposted videos!!")
        video_id, video_data = unposted_videos[0]
        file_path = video_data["filepath"]
        successful_person = video_data["successful_person"]
    else:
        print("No unposted videos found, getting new ones")

        # get successful name
        successful_person = get_successful_person()

        video = Video(successful_person, db)
        video_id = video.get_videos()
        video_data = db.videos[video_id]
        file_path = video_data["filepath"]

    print(f"Posting video {video_id} with title {video_data['title']}")
    xposter = XPoster()
    post_id = xposter.post(file_path, successful_person, video_data["webpage_url"])
    print(f"Posted video {video_id}")
    # update the video with the post_id
    db.update_video(video_id, post_id)
