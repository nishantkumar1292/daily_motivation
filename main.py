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

    def migrate_from_json(self, json_file="db.json"):
        """Migrate data from JSON database to SQLite"""
        if not os.path.exists(json_file):
            print(f"JSON file {json_file} not found. Nothing to migrate.")
            return

        print(f"Migrating data from {json_file} to SQLite...")

        with open(json_file, "r") as f:
            json_videos = json.load(f)

        migrated_count = 0
        for video_id, video_data in json_videos.items():
            self.add_video(video_data)
            migrated_count += 1

        print(f"Successfully migrated {migrated_count} videos to SQLite database.")

        # Optionally backup the JSON file
        backup_file = f"{json_file}.backup"
        import shutil
        shutil.copy2(json_file, backup_file)
        print(f"Original JSON file backed up as {backup_file}")

        return migrated_count

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

    def get_videos(self):
        query = f"motivational interview or speech or talk + {self.successful_person}"

        # Specify exact output path
        ydl_opts = {
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            # Use default format selection to avoid format availability issues
            'compat_opts': ['prefer-vp9-sort'],  # Revert to pre-2024.11.04 format prioritization
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
    xposter = XPoster()
    post_id = xposter.post(file_path, successful_person, video_data["webpage_url"])
    print(f"Posted video {video_id}")
    # update the video with the post_id
    db.update_video(video_id, post_id)
