import os
import subprocess
import re
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


def load_config():
    config_file = "config.json"
    if not os.path.exists(config_file):
        print("Error: config.json not found in the root directory. Please create it with required settings.")
        sys.exit(1)
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)

def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)]
    )

def safe_filename(s):
    # Remove characters that are not allowed in filenames
    return re.sub(r'[\\/*?:"<>|]', "", s)

def get_video_title(url):
    result = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error retrieving title for video: {url}")
        return None
    return result.stdout.strip()

def download_file(url, format_option, output_template, max_retries):
    command = [
        "yt-dlp",
        "-f", format_option,
        "--continue",
        "-o", output_template,
        url
    ]
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        logging.info(f"Attempt {attempt} for: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return True, ""
        else:
            logging.error(f"Attempt {attempt} failed for {url}: {result.stderr}")
    return False, result.stderr

def merge_files(video_file, audio_file, output_file):
    command = [
        "ffmpeg",
        "-i", video_file,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        output_file,
        "-y"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"FFmpeg merge failed: {result.stderr}")
        return False, result.stderr
    return True, ""

def download_and_process(url, output_dir, temp_dir, index, total, config):
    mode = config.get("mode", "both")
    output_format = config.get("output_format", "mp4")
    max_retries = config.get("retries", 3)
    
    logging.info(f"Processing video {index} of {total}...")
    title = get_video_title(url)
    if not title:
        logging.error(f"Skipping video {index}: Could not retrieve title.")
        return
    safe_title_str = safe_filename(title)

    video_temp = os.path.join(temp_dir, f"{safe_title_str}_video.%(ext)s")
    audio_temp = os.path.join(temp_dir, f"{safe_title_str}_audio.%(ext)s")
    final_output = os.path.join(output_dir, f"{safe_title_str}.{output_format}")

    if mode == "both":
        # Download video and audio streams separately
        success_video, err_video = download_file(url, "bestvideo", video_temp, max_retries)
        if not success_video:
            logging.error(f"Error downloading video stream for '{safe_title_str}': {err_video}")
            return
        success_audio, err_audio = download_file(url, "bestaudio", audio_temp, max_retries)
        if not success_audio:
            logging.error(f"Error downloading audio stream for '{safe_title_str}': {err_audio}")
            return

        # Locate the downloaded temporary files (yt-dlp assigns the proper extension)
        video_file = None
        audio_file = None
        for file in os.listdir(temp_dir):
            if file.startswith(f"{safe_title_str}_video."):
                video_file = os.path.join(temp_dir, file)
            if file.startswith(f"{safe_title_str}_audio."):
                audio_file = os.path.join(temp_dir, file)
        if not video_file or not audio_file:
            logging.error(f"Missing downloaded file(s) for '{safe_title_str}'.")
            return

        logging.info(f"Merging video and audio for '{safe_title_str}' into {final_output}...")
        merge_success, merge_err = merge_files(video_file, audio_file, final_output)
        if not merge_success:
            logging.error(f"Error merging files for '{safe_title_str}': {merge_err}")
            return
        else:
            logging.info(f"Successfully merged and saved: {final_output}")
        # Clean up temporary files
        try:
            os.remove(video_file)
            os.remove(audio_file)
        except Exception as e:
            logging.error(f"Error cleaning up temporary files for '{safe_title_str}': {e}")

    elif mode == "audio":
        # Download only the best audio stream
        success_audio, err_audio = download_file(url, "bestaudio", audio_temp, max_retries)
        if not success_audio:
            logging.error(f"Error downloading audio stream for '{safe_title_str}': {err_audio}")
            return
        audio_file = None
        for file in os.listdir(temp_dir):
            if file.startswith(f"{safe_title_str}_audio."):
                audio_file = os.path.join(temp_dir, file)
                break
        if not audio_file:
            logging.error(f"Missing audio file for '{safe_title_str}'.")
            return
        try:
            os.rename(audio_file, final_output)
            logging.info(f"Audio saved: {final_output}")
        except Exception as e:
            logging.error(f"Error moving audio file for '{safe_title_str}': {e}")

    elif mode == "video":
        # Download only the best video stream
        success_video, err_video = download_file(url, "bestvideo", video_temp, max_retries)
        if not success_video:
            logging.error(f"Error downloading video stream for '{safe_title_str}': {err_video}")
            return
        video_file = None
        for file in os.listdir(temp_dir):
            if file.startswith(f"{safe_title_str}_video."):
                video_file = os.path.join(temp_dir, file)
                break
        if not video_file:
            logging.error(f"Missing video file for '{safe_title_str}'.")
            return
        try:
            os.rename(video_file, final_output)
            logging.info(f"Video saved: {final_output}")
        except Exception as e:
            logging.error(f"Error moving video file for '{safe_title_str}': {e}")

    else:
        logging.error(f"Unknown mode: {mode}")
        return

def main():
    config = load_config()

    # Ensure required configuration keys are present
    required_keys = ["playlist_url", "output", "parallel", "output_format", "mode", "retries"]
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required configuration key: {key}")
            sys.exit(1)
    
    playlist_url = config["playlist_url"]
    output_dir = config["output"]
    temp_dir = os.path.join(output_dir, "temp")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    log_file = os.path.join(output_dir, "download.log")
    setup_logging(log_file)
    
    # Extract video URLs from the playlist using yt-dlp's --flat-playlist
    extract_command = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "url",
        playlist_url
    ]
    result = subprocess.run(extract_command, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error extracting playlist: {result.stderr}")
        sys.exit(1)
    video_urls = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    total_videos_in_playlist = len(video_urls)
    if total_videos_in_playlist == 0:
        logging.error("No videos found in the playlist.")
        sys.exit(1)
    
    # Determine download range (1-based indexing)
    start = config.get("start", 1)
    end = config.get("end", total_videos_in_playlist)
    if end == 0:  # if end is 0, download until the end
        end = total_videos_in_playlist
    if start < 1 or end > total_videos_in_playlist or start > end:
        logging.error("Invalid range specified. Ensure 1 <= start <= end <= total videos in playlist.")
        sys.exit(1)
    
    selected_urls = video_urls[start-1:end]
    total_selected = len(selected_urls)
    logging.info(f"Found {total_videos_in_playlist} videos in the playlist. Downloading videos {start} to {end} ({total_selected} videos).")
    
    parallel = config.get("parallel", 1)
    
    if parallel > 1:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(download_and_process, url, output_dir, temp_dir, idx, total_selected, config): url 
                       for idx, url in enumerate(selected_urls, start=1)}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error processing a video: {e}")
    else:
        for idx, url in enumerate(tqdm(selected_urls, desc="Overall Progress"), start=1):
            download_and_process(url, output_dir, temp_dir, idx, total_selected, config)

if __name__ == "__main__":
    # Temporary basic logging until config is loaded
    logging.basicConfig(level=logging.INFO)
    logging.info("Disclaimer: This tool is for downloading content only for lawful purposes and in accordance with YouTube's terms of service.")
    main()
