import os
import tweepy
import requests
import json
import time
from requests_oauthlib import OAuth1
import openai
import whisper

class InspiringPostGenerator:
    def __init__(self, openai_api_key=None, whisper_model_size="base"):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.whisper_model_size = whisper_model_size
        self._whisper_model = None

    def transcribe(self, video_path):
        if self._whisper_model is None:
            self._whisper_model = whisper.load_model(self.whisper_model_size)
        result = self._whisper_model.transcribe(video_path)
        return result["text"]

    def generate_post(self, transcript, person_name):
        openai.api_key = self.openai_api_key
        prompt = f"""
You are a world-class motivational storyteller and social media expert.

Given the following transcript from a motivational video featuring {person_name}, write an inspiring, story-like social media post. The post should:
- Summarize the key message and emotional highlights of the video
- Highlight why {person_name} is so motivating
- Be compelling and make readers want to watch the video
- Be concise (max 280 characters), but vivid and emotionally engaging

Transcript:
"""
        prompt += transcript + "\n\nSocial media post:"
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a world-class motivational storyteller and social media expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=120,
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()

    def generate_inspiring_post_from_video(self, video_path, person_name):
        transcript = self.transcribe(video_path)
        return self.generate_post(transcript, person_name)

class XPoster:
    def __init__(self, community_id=None, db=None, post_generator=None):
        # Twitter API credentials
        self.api_key = os.getenv("TWITTER_API_KEY")
        self.api_secret = os.getenv("TWITTER_API_SECRET")
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self.access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        # Community ID for posting to specific communities
        self.community_id = community_id or os.getenv("TWITTER_COMMUNITY_ID")

        # Database instance for caching media_ids
        self.db = db

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

        self.post_generator = post_generator or InspiringPostGenerator()

    def wait_for_media_processing(self, media_id):
        """Wait for Twitter to finish processing the uploaded media"""
        print(f"Waiting for media {media_id} to finish processing...")

        max_attempts = 60  # Maximum wait time of ~60 seconds
        for attempt in range(max_attempts):
            try:
                result = self.api.get_media_upload_status(media_id)
                processing_info = result.processing_info

                state = processing_info.get('state', 'succeeded')

                if state == 'succeeded':
                    print("Media processing complete!")
                    return True
                elif state == 'failed':
                    error = processing_info.get('error', {})
                    error_name = error.get('name', 'Unknown error')
                    error_message = error.get('message', 'No error message')
                    print(f"Media processing failed: {error_name} - {error_message}")
                    raise Exception(f"Media processing failed: {error_name} - {error_message}")
                else:
                    # Still processing
                    check_after_secs = processing_info.get('check_after_secs', 1)
                    print(f"Processing... (state: {state}, check again in {check_after_secs}s)")
                    time.sleep(check_after_secs)
            except Exception as e:
                if "processing_info" in str(e).lower():
                    # If no processing_info, assume it's done
                    print("No processing info available - assuming media is ready")
                    return True
                else:
                    raise e

        raise Exception("Media processing timeout - took too long to process")

    def post(self, video_path, successful_person, video_url, video_id=None):
        try:
            # Always upload video fresh since media_ids expire quickly
            print("Uploading video...")
            media = self.api.media_upload(video_path, chunked=True, media_category="amplify_video")
            media_id = media.media_id

            # Wait for video processing to complete
            self.wait_for_media_processing(media_id)

            # Use AI to generate an inspiring post
            print("Generating inspiring post text using AI...")
            text = self.post_generator.generate_inspiring_post_from_video(video_path, successful_person)
            print(f"Generated post: {text}")

            # Use direct API call for community posting
            if self.community_id:
                print(f"Posting to Twitter Community ID: {self.community_id}")
                post_id = self._post_to_community(text, media_id, video_url)
                return post_id
            else:
                print("Posting as regular tweet")
                post = self.client.create_tweet(text=text, media_ids=[media_id])

                # add comment with video link
                self.client.create_tweet(
                    text=f"Video source: {video_url}",
                    in_reply_to_tweet_id=post.data["id"]
                )
                return post.data["id"]
        except Exception as e:
            print(f"Error posting video: {e}")
            raise e

    def _post_to_community(self, text, media_id, video_url):
        """Post directly to Twitter Community using X API v2 with OAuth 1.0a"""
        url = "https://api.twitter.com/2/tweets"

        # Use OAuth 1.0a authentication instead of Bearer token for community posting
        auth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

        payload = {
            "text": text,
            "community_id": self.community_id,
            "media": {
                "media_ids": [str(media_id)]
            }
        }

        print(f"Attempting community post with payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(url, json=payload, auth=auth)

            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")

            if response.status_code == 500:
                print("Community posting failed with 500 error - falling back to regular tweet")
                return self._fallback_to_regular_post(text, media_id, video_url)

            response.raise_for_status()

            result = response.json()
            post_id = result["data"]["id"]

            print(f"Successfully posted to community!")
            print(f"Post ID: {post_id}")

            # Add comment with video source
            self._post_reply(video_url, post_id)

            return post_id

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error posting to community: {e}")
            print(f"Response: {response.text}")
            print("Falling back to regular tweet posting...")
            return self._fallback_to_regular_post(text, media_id, video_url)
        except Exception as e:
            print(f"Error posting to community: {e}")
            print("Falling back to regular tweet posting...")
            return self._fallback_to_regular_post(text, media_id, video_url)

    def _fallback_to_regular_post(self, text, media_id, video_url):
        """Fallback to regular tweet if community posting fails"""
        print("Posting as regular tweet instead...")

        try:
            post = self.client.create_tweet(text=text, media_ids=[str(media_id)])

            # add comment with video link
            self.client.create_tweet(
                text=f"Video source: {video_url}",
                in_reply_to_tweet_id=post.data["id"]
            )

            print(f"Successfully posted as regular tweet: {post.data['id']}")
            return post.data["id"]
        except Exception as e:
            print(f"Error posting regular tweet: {e}")
            raise e

    def _post_reply(self, video_url, reply_to_id):
        """Post a reply with the video source URL"""
        url = "https://api.twitter.com/2/tweets"

        # Use OAuth 1.0a authentication for consistency with community posting
        auth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

        payload = {
            "text": f"Video source: {video_url}",
            "reply": {
                "in_reply_to_tweet_id": reply_to_id
            }
        }

        try:
            response = requests.post(url, json=payload, auth=auth)
            response.raise_for_status()
            result = response.json()
            print(f"Successfully posted source URL reply: {result['data']['id']}")
        except Exception as e:
            print(f"Warning: Could not post source URL reply: {e}")
            # Don't raise here, as the main post succeeded

    def get_joined_communities(self):
        """Get list of communities the authenticated user has joined"""
        try:
            # Note: This requires Twitter API v2 with appropriate permissions
            # You might need elevated access for this endpoint
            response = self.client.get_owned_lists()
            if response.data:
                print("Available communities/lists:")
                for community in response.data:
                    print(f"  ID: {community.id} - Name: {community.name}")
            else:
                print("No communities found or insufficient permissions")
            return response.data if response.data else []
        except Exception as e:
            print(f"Error fetching communities: {e}")
            print("Note: Community access might require elevated Twitter API permissions")
            return []

    def post_text(self, text):
        """Post just text to community or regular tweet"""
        try:
            # Use direct API call for community posting
            if self.community_id:
                print(f"Posting text to Twitter Community ID: {self.community_id}")
                post_id = self._post_text_to_community(text)
                return post_id
            else:
                print("Posting as regular tweet")
                post = self.client.create_tweet(text=text)
                return post.data["id"]
        except Exception as e:
            print(f"Error posting text: {e}")
            raise e

    def _post_text_to_community(self, text):
        """Post text directly to Twitter Community using X API v2 with OAuth 1.0a"""
        url = "https://api.twitter.com/2/tweets"

        # Use OAuth 1.0a authentication instead of Bearer token for community posting
        auth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret,
        )

        payload = {
            "text": text,
            "community_id": self.community_id
        }

        print(f"Attempting community text post with payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(url, json=payload, auth=auth)

            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")

            if response.status_code == 500:
                print("Community posting failed with 500 error - falling back to regular tweet")
                return self._fallback_to_regular_text_post(text)

            response.raise_for_status()

            result = response.json()
            post_id = result["data"]["id"]

            print(f"Successfully posted text to community!")
            print(f"Post ID: {post_id}")

            return post_id

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error posting to community: {e}")
            print(f"Response: {response.text}")
            print("Falling back to regular tweet posting...")
            return self._fallback_to_regular_text_post(text)
        except Exception as e:
            print(f"Error posting to community: {e}")
            print("Falling back to regular tweet posting...")
            return self._fallback_to_regular_text_post(text)

    def _fallback_to_regular_text_post(self, text):
        """Fallback to regular tweet if community posting fails"""
        print("Posting as regular tweet instead...")

        try:
            post = self.client.create_tweet(text=text)
            print(f"Successfully posted as regular tweet: {post.data['id']}")
            return post.data["id"]
        except Exception as e:
            print(f"Error posting regular tweet: {e}")
            raise e

class WhatsAppPoster:
    def __init__(self):
        pass

    def post(self, video_path, successful_person):
        try:
            text = f"Motivational stuff from {successful_person.title()}"
        except Exception as e:
            print(f"Error posting video to WhatsApp: {e}")
            raise e