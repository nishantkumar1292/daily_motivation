# Motivational Video Poster
This repository contains a script that posts motivational videos to X (Twitter) daily.

## How to use it?
1. Create a `.env` file in the root of the repository and add the following variables:
    - `TWITTER_API_KEY`
    - `TWITTER_API_SECRET`
    - `TWITTER_ACCESS_TOKEN`
    - `TWITTER_ACCESS_TOKEN_SECRET`
    - `TWITTER_BEARER_TOKEN`
    - `TWITTER_COMMUNITY_ID` # incase you want to post to a community
    - `OPENAI_API_KEY` # for generating the post
2. Install the dependencies. Preferably do this in a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```
3. Run the script.
    ```bash
    python main.py
    ```

## What am I doing here?
1. First Goal: The goal is to create a X handle that posts a motivational video every day.
2. How do I do it?
    1. Use yt-dlp to download the video
    1. Build a service to post the video to X
3. Second Goal: Build a service to post the videos to WhatsApp daily.


## Next
1. Cleanup and simplify the code. For example, tweepy is not needed.
2. Expand the search if all of the videos are more than 10 minutes.
3. Create a cron job that does these posts regularly.
4. Start a whatsapp channel and post there as well.
4. Can I create interview like videos from X posts, using AI?
5. Can I tag the person in the video? I think I need to predefine the X handle for the person.
6. Can I take a large video and find an interesting part of 10 minutes (10 minutes is the X.com limit) and then post that?
