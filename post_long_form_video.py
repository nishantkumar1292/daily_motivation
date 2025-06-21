import json
import yt_dlp
import os
import whisper
import openai
import subprocess
import yaml

from text_matching import find_robust_timestamps
from poster import XPoster

def download_video(video_url, video_directory):
    ydl_opts = {
        'outtmpl': f'{video_directory}/%(title)s.%(ext)s',
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'postprocessor_args': {
            'ffmpeg': ['-c:v', 'libx264', '-c:a', 'aac', '-preset', 'medium']
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        download_result = ydl.extract_info(video_url, download=True)
        actual_filename = ydl.prepare_filename(download_result)

        if not os.path.exists(actual_filename):
            raise Exception(f"Download failed - file not found: {actual_filename}")

        return actual_filename

def transcribe_video(video_path, model_size="base", transcription_file=None):
    """
    Transcribe video with different model sizes and progress indication.

    Args:
        video_path: Path to video file
        model_size: Whisper model size. Options:
            - "tiny": Fastest, least accurate (~39x realtime)
            - "base": Good balance of speed/accuracy (~16x realtime) [DEFAULT]
            - "small": Better accuracy, slower (~6x realtime)
            - "medium": Even better accuracy (~2x realtime)
            - "large": Best accuracy, slowest (~1x realtime)
    """
    # check if transcription file exists
    if os.path.exists(transcription_file):
        with open(transcription_file, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"Loading Whisper model '{model_size}'...")
    model = whisper.load_model(model_size)

    print(f"Transcribing video: {os.path.basename(video_path)}")
    print("This may take a few minutes depending on video length...")

    result = model.transcribe(video_path, word_timestamps=True, verbose=True)

    if transcription_file:
        with open(transcription_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"Transcription saved to {transcription_file}")

    return result

def extract_narratives(video_transcription, narratives_file=None):
    """Uses OpenAI's GPT models to find powerful narrative snippets in the transcript."""
    print("\nConnecting to OpenAI API to find powerful narratives...")

    # check if narratives file exists
    if os.path.exists(narratives_file):
        with open(narratives_file, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception as e:
        print(f"Failed to initialize OpenAI client. Is the API key set correctly? Error: {e}")
        return None

    system_prompt = """
    You are an expert content strategist specializing in extracting powerful, resonant content from interviews and podcasts with successful people.

    Your goal is to identify 5-10 distinct themes or ideas that will deeply resonate with audiences seeking inspiration, growth, and success insights.

    Look for these types of universally resonant themes:

    **STRUGGLE & OVERCOMING:**
    - "The Lowest Point That Changed Everything"
    - "When Everyone Said No But I Kept Going"
    - "The Mistake That Became My Greatest Teacher"
    - "How I Turned Rejection Into Motivation"

    **MINDSET & PHILOSOPHY:**
    - "The One Belief That Transformed My Life"
    - "Why I Stopped Caring What Others Think"
    - "The Hard Truth About Success Nobody Tells You"
    - "My Daily Habit That Changed Everything"

    **PRACTICAL WISDOM:**
    - "The Best Advice I Wish I Had at 25"
    - "What I Do When I Feel Like Giving Up"
    - "The Question That Guides All My Decisions"
    - "How I Handle Criticism and Doubt"

    **SUCCESS PRINCIPLES:**
    - "The Skill That Made Me Irreplaceable"
    - "Why I Work Differently Than Everyone Else"
    - "The Investment That Paid Off Forever"
    - "My Unconventional Approach to [Industry]"

    **LIFE LESSONS:**
    - "What Money Can't Buy (And What It Can)"
    - "The Relationship Advice I Wish I Knew Earlier"
    - "How I Balance Ambition and Happiness"
    - "The Legacy I Actually Want to Leave"

    **FUTURE & VISION:**
    - "The Opportunity Everyone Is Missing"
    - "Why [Industry/Trend] Will Change Everything"
    - "The Problem I'm Obsessed With Solving"
    - "Where I See the World Going Next"

    Each snippet should:
    - Focus on ONE clear, relatable theme that speaks to human ambition, growth, or wisdom
    - Be emotionally compelling and shareable
    - Contain complete thoughts that don't require external context
    - Include specific stories, examples, or actionable insights
    - Be no longer than 10 minutes
    - Have natural speaking flow with clear beginning and end points
    - Avoid topics that are too niche or require specialized knowledge
    - If there is a question that the person is answering, also include the question in the snippet. Basically start the snippet with the question and end with the answer.

    Prioritize content that makes viewers think: "I needed to hear this" or "This changes how I see [topic]"

    Return JSON with:
    {{
        "snippets": [
            {{
                "title": "Compelling, click-worthy title that promises value",
                "theme": "The core human theme/lesson",
                "summary": "Why this resonates and what viewers will gain",
                "start_sentence": "Exact first sentence from transcript. Keep the exact sentence as it is. DO NOT CHANGE IT.",
                "end_sentence": "Exact last sentence from transcript. Keep the exact sentence as it is. DO NOT CHANGE IT.",
                "resonance_factor": "Why this will connect with people (motivation/inspiration/practical value)"
            }}
        ]
    }}

    Focus on extracting wisdom that transcends the speaker's specific industry or circumstances - universal insights that apply to anyone pursuing success, growth, or fulfillment.
    """

    user_prompt = f"Analyze this interview/podcast transcript and extract the most resonant themes that will inspire and help people: --- {video_transcription['text']} ---"

    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        response_content = response.choices[0].message.content
        narratives = json.loads(response_content)

        print("Successfully received and parsed narratives from OpenAI.")

        if narratives_file:
            with open(narratives_file, "w", encoding="utf-8") as f:
                json.dump(narratives.get('snippets', []), f, indent=2)

        return narratives.get('snippets', [])

    except openai.APIError as e:
        print(f"An OpenAI API error occurred: {e}")
    except json.JSONDecodeError:
        print("Failed to decode JSON from the OpenAI response.")
        print("LLM Response Text:", response_content if 'response_content' in locals() else "No response content received.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None

def extract_snippet_timestamps(video_transcription, narratives, snippet_timestamps_file=None):
    # check if snippet timestamps file exists
    if os.path.exists(snippet_timestamps_file):
        with open(snippet_timestamps_file, 'r') as f:
            return json.load(f)

    snippet_timestamps = []

    for narrative in narratives:
        start_time, _ = find_robust_timestamps(
            video_transcription,
            narrative["start_sentence"]
        )
        _, end_time = find_robust_timestamps(
            video_transcription,
            narrative["end_sentence"]
        )

        if start_time is not None and end_time is not None:
            snippet_timestamps.append({
                "title": narrative["title"],
                "start_time": start_time,
                "end_time": end_time,
                "theme": narrative["theme"],
                "summary": narrative["summary"]
            })

    if snippet_timestamps_file:
        with open(snippet_timestamps_file, 'w') as f:
            json.dump(snippet_timestamps, f, indent=2)

    return snippet_timestamps

def cleanup_snippet_timestamps(snippet_timestamps):
    # sort snippet timestamps by start time
    snippet_timestamps.sort(key=lambda x: x['start_time'])
    cleaned_snippet_timestamps = []

    for i, snippet in enumerate(snippet_timestamps):
        if i == 0:
            cleaned_snippet_timestamps.append(snippet)
            continue

        if snippet['start_time'] > cleaned_snippet_timestamps[-1]['end_time']:
            cleaned_snippet_timestamps.append(snippet)

    return cleaned_snippet_timestamps

def extract_video_snippets(video_path, snippet_timestamps, snippets_metadata_file):
    """Extract video snippets using ffmpeg based on timestamps"""

    output_folder = "extracted_snippets"

    if os.path.exists(snippets_metadata_file):
        with open(snippets_metadata_file, 'r') as f:
            extracted_files = json.load(f)
        return extracted_files

    os.makedirs(output_folder, exist_ok=True)

    extracted_files = []

    for i, snippet in enumerate(snippet_timestamps, 1):
        print(f"\n📹 Processing snippet {i}/{len(snippet_timestamps)}: {snippet['title']}")

        # Create safe filename
        safe_title = "".join(c for c in snippet['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]

        output_file = os.path.join(output_folder, f"{safe_title}.mp4")

        # Calculate duration
        duration = snippet['end_time'] - snippet['start_time']

        if os.path.exists(output_file):
            print(f"✗ Skipping {snippet['title']} because it already exists")
            continue

        # FFmpeg command for accurate cutting
        cmd = [
            'ffmpeg',
            '-ss', str(snippet['start_time']),
            '-i', video_path,
            '-t', str(duration),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'fast',
            '-crf', '23',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            output_file
        ]

        print(f"Extracting: {snippet['title']} ({snippet['start_time']:.1f}s - {snippet['end_time']:.1f}s)")

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✓ Saved to: {output_file}")

            extracted_files.append({
                'title': snippet['title'],
                'theme': snippet['theme'],
                'summary': snippet['summary'],
                'start_time': snippet['start_time'],
                'end_time': snippet['end_time'],
                'duration': duration,
                'file': output_file
            })

        except subprocess.CalledProcessError as e:
            print(f"✗ Error extracting {snippet['title']}: {e}")

    # Save metadata
    with open(snippets_metadata_file, 'w') as f:
        json.dump(extracted_files, f, indent=2)

    print(f"\n✅ Extraction complete! {len(extracted_files)} snippets extracted to: {output_folder}")
    print(f"📄 Metadata saved to: {snippets_metadata_file}")

    return extracted_files

def post_video_snippets(snippets_metadata, video_url, video_speaker_x_handle, community_id=None):
    poster = XPoster(community_id=community_id)
    previous_post_id = None

    for snippet in snippets_metadata:
        # skip if the duration is less than 60 seconds
        if snippet['duration'] < 60:
            continue

        text = f"{snippet['title']}\n\n{snippet['summary']}"
        media = poster.api.media_upload(snippet['file'], chunked=True, media_category="amplify_video")
        media_id = media.media_id

        if previous_post_id:
            # Post as reply to previous tweet
            post = poster.client.create_tweet(
                text=text,
                media_ids=[media_id],
                in_reply_to_tweet_id=previous_post_id
            )
            previous_post_id = post.data["id"]
        else:
            # First post in thread
            intro_text = f"I recently watched a video from @{video_speaker_x_handle} and I found it interesting. Sharing some important snippets in the thread below:\n\n"
            full_text = intro_text + text

            if community_id:
                # Use direct community posting for first post
                post_id = poster._post_to_community(full_text, media_id, post_reply=False)
                previous_post_id = post_id
            else:
                post = poster.client.create_tweet(
                    text=full_text,
                    media_ids=[media_id]
                )
                previous_post_id = post.data["id"]

    # Add source video link as final reply
    poster.client.create_tweet(
        text=f"Source: {video_url}",
        in_reply_to_tweet_id=previous_post_id
    )

if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    video_url = config["video_url"]
    video_speaker_x_handle = config["video_speaker_x_handle"]
    community_id = config.get("community_id")

    # Setup files and directories
    video_id = video_url.split("v=")[1]
    video_directory = f"videos/{video_id}"
    os.makedirs(video_directory, exist_ok=True)

    transcription_file = f"{video_directory}/transcription.json"
    narratives_file = f"{video_directory}/narratives.json"
    snippet_timestamps_file = f"{video_directory}/snippet_timestamps.json"
    snippets_metadata_file = f"{video_directory}/snippets_metadata.json"

    # download video
    video_path = download_video(video_url, video_directory)

    # transcribe video
    video_transcription = transcribe_video(video_path, transcription_file=transcription_file)

    # extract narratives
    narratives = extract_narratives(video_transcription, narratives_file=narratives_file)

    # extract snippet timestamps
    snippet_timestamps = extract_snippet_timestamps(video_transcription, narratives, snippet_timestamps_file=snippet_timestamps_file)

    # cleanup snippets to not have intersecting timestamps
    snippet_timestamps = cleanup_snippet_timestamps(snippet_timestamps)

    # extract video snippets
    snippets_metadata = extract_video_snippets(video_path, snippet_timestamps, snippets_metadata_file=snippets_metadata_file)

    # post video snippets
    post_video_snippets(snippets_metadata, video_url, video_speaker_x_handle, community_id)
