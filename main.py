import json
import os
import random
import sqlite3
import yt_dlp
from dotenv import load_dotenv
from poster import XPoster

load_dotenv()

class Database:
    def __init__(self, source_file=None):
        self.db_file = source_file or "db.sqlite"
        self.init_db()

    def init_db(self):
        """Initialize the SQLite database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_file)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                title TEXT,
                webpage_url TEXT,
                filepath TEXT,
                successful_person TEXT,
                post_id TEXT,
                x_media_id TEXT,
                data TEXT  -- JSON blob for any additional data
            )
        ''')
        conn.commit()
        conn.close()

    def add_video(self, video):
        """Add a video to the database"""
        conn = sqlite3.connect(self.db_file)
        conn.execute('''
            INSERT OR REPLACE INTO videos
            (id, title, webpage_url, filepath, successful_person, post_id, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            video["id"],
            video.get("title"),
            video.get("webpage_url"),
            video.get("filepath"),
            video.get("successful_person"),
            video.get("post_id"),
            json.dumps(video)  # Store complete video data as JSON
        ))
        conn.commit()
        conn.close()

    def update_video(self, video_id, post_id):
        """Update a video's post_id"""
        conn = sqlite3.connect(self.db_file)
        # First get the current data to update the JSON blob
        cursor = conn.execute('SELECT data FROM videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        if row:
            video_data = json.loads(row[0])
            video_data["post_id"] = post_id
            conn.execute('''
                UPDATE videos
                SET post_id = ?, data = ?
                WHERE id = ?
            ''', (post_id, json.dumps(video_data), video_id))
        conn.commit()
        conn.close()

    def update_video_media_id(self, video_id, media_id):
        """Update a video's x_media_id"""
        conn = sqlite3.connect(self.db_file)
        # First get the current data to update the JSON blob
        cursor = conn.execute('SELECT data FROM videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        if row:
            video_data = json.loads(row[0])
            video_data["x_media_id"] = media_id
            conn.execute('''
                UPDATE videos
                SET x_media_id = ?, data = ?
                WHERE id = ?
            ''', (media_id, json.dumps(video_data), video_id))
        conn.commit()
        conn.close()

    def get_unposted_videos(self):
        """Get videos that haven't been posted yet"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute('SELECT id, data FROM videos WHERE post_id IS NULL OR post_id = ""')
        result = []
        for row in cursor.fetchall():
            video_id = row[0]
            video_data = json.loads(row[1])
            result.append((video_id, video_data))
        conn.close()
        return result

    @property
    def videos(self):
        """Provide backward compatibility by simulating the old videos dict"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute('SELECT id, data FROM videos')
        videos_dict = {}
        for row in cursor.fetchall():
            video_id = row[0]
            video_data = json.loads(row[1])
            videos_dict[video_id] = video_data
        conn.close()
        return videos_dict

    def get_video_media_id(self, video_id):
        """Get the cached media_id for a video"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute('SELECT x_media_id FROM videos WHERE id = ?', (video_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else None

    def delete_video(self, video_id):
        """Delete a video from the database"""
        conn = sqlite3.connect(self.db_file)
        conn.execute('DELETE FROM videos WHERE id = ?', (video_id,))
        conn.commit()
        conn.close()
        print(f"Deleted video {video_id} from database")

    def view_records(self):
        """View all records in the database in a formatted way"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.execute('''
            SELECT id, title, successful_person, post_id
            FROM videos
            ORDER BY id
        ''')

        print("\n=== DATABASE RECORDS ===")
        for row in cursor.fetchall():
            video_id, title, successful_person, post_id = row
            status = "POSTED" if post_id else "UNPOSTED"
            print(f"ID: {video_id}")
            print(f"Title: {title}")
            print(f"Person: {successful_person}")
            print(f"Status: {status}")
            if post_id:
                print(f"Post ID: {post_id}")
            print("-" * 50)

        conn.close()

class Video:
    def __init__(self, successful_person, db, num_videos=1, output_dir="videos"):
        self.successful_person = successful_person
        self.num_videos = num_videos
        self.db = db
        self.output_dir = output_dir

        # create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def _duration_filter(self, info_dict):
        """Filter videos by duration - only allow videos under 10 minutes for Twitter"""
        duration = info_dict.get('duration')
        if duration is None:
            # If duration is unknown, allow it (some videos don't have duration info)
            return None

        # Twitter limit: 10 minutes = 600 seconds
        max_duration = 600

        if duration > max_duration:
            minutes = duration // 60
            seconds = duration % 60
            print(f"    SKIPPING: Video too long ({minutes}m {seconds}s) - Twitter limit is 10 minutes")
            return f"Video duration {duration}s exceeds Twitter limit of {max_duration}s"

        return None  # None means accept the video

    def get_videos(self):
        query = f"motivational interview or speech or talk + {self.successful_person}"

        # Specify exact output path and duration limit for Twitter
        ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            # Post-processors to ensure MP4 with H.264 codec for Twitter compatibility
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Force re-encoding to H.264 if needed
            'postprocessor_args': {
                'ffmpeg': ['-c:v', 'libx264', '-c:a', 'aac', '-preset', 'medium']
            },
            # Only download videos under 10 minutes (600 seconds) for Twitter compatibility
            'match_filter': self._duration_filter,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch{self.num_videos * 3}:{query}", download=False)

            print(f"Found {len(result['entries'])} potential videos for {self.successful_person}")

            for i, entry in enumerate(result["entries"]):
                video_id = entry["id"]
                video_title = entry.get("title", "Unknown Title")

                # Check if video is already in database
                if video_id in self.db.videos:
                    print(f"  [{i+1}] SKIP: Video already in database - {video_title[:60]}...")

                    # Double-check if the file actually exists on disk
                    existing_video = self.db.videos[video_id]
                    if existing_video.get("filepath") and os.path.exists(existing_video["filepath"]):
                        continue
                    else:
                        print(f"    WARNING: Database entry exists but file missing: {existing_video.get('filepath')}")
                        print(f"    Re-downloading this video...")

                print(f"  [{i+1}] DOWNLOADING: {video_title[:60]}...")

                try:
                    # download the video and get the actual file path
                    download_result = ydl.extract_info(entry["webpage_url"], download=True)
                    actual_filename = ydl.prepare_filename(download_result)

                    # Verify the file was actually downloaded
                    if not os.path.exists(actual_filename):
                        print(f"    ERROR: Download failed - file not found: {actual_filename}")
                        continue

                    # add filepath to entry
                    entry["filepath"] = actual_filename
                    # add successful person to entry
                    entry["successful_person"] = self.successful_person
                    self.db.add_video(entry)

                    print(f"    SUCCESS: Downloaded and saved to database")
                    print(f"    File: {actual_filename}")
                    return entry["id"]

                except Exception as e:
                    print(f"    ERROR: Failed to download video {video_id}: {str(e)}")
                    continue

            print(f"ERROR: No new videos found for {self.successful_person} after checking {len(result['entries'])} videos")
            return None


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

        if video_id is None:
            print("ERROR: Could not download any new videos. Exiting.")
            exit(1)

        video_data = db.videos[video_id]
        file_path = video_data["filepath"]

    print(f"Posting video {video_id} with title {video_data['title']}")

    # Initialize XPoster - will use community_id from environment variable if set
    xposter = XPoster(db=db)
    post_id = xposter.post(file_path, successful_person, video_data["webpage_url"], video_id=video_id)
    print(f"Posted video {video_id}")
    # update the video with the post_id
    db.update_video(video_id, post_id)
