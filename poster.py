import os
import tweepy

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

    def post(self, video_path, successful_person, video_url):
        try:
            media = self.api.media_upload(video_path, chunked=True, media_category="amplify_video")

            # TODO: get a more interesting text from analyzing the video
            text = f"Motivational stuff from {successful_person.title()}"
            # post the media
            post = self.client.create_tweet(text=text, media_ids=[media.media_id])
            # add comment with video link
            self.client.create_tweet(text=f"Video source: {video_url}", in_reply_to_tweet_id=post.data["id"])
            return post.data["id"]
        except Exception as e:
            print(f"Error posting video: {e}")
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