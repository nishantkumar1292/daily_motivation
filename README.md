# Motivational Video Poster
This repository contains a script that posts motivational videos to X (Twitter) daily.

## How to use it?
1. Create a `.env` file in the root of the repository and add the following variables:
    - `TWITTER_API_KEY`
    - `TWITTER_API_SECRET`
    - `TWITTER_ACCESS_TOKEN`
    - `TWITTER_ACCESS_TOKEN_SECRET`
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
1. Create an X channel, and create a cron job that does these posts regularly.
2. Start a whatsapp channel and post there as well.
