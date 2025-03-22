# This is Test File, just for testing purpose

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
        print("Error: config.json not found. Please create it with the required settings.")
        sys.exit(1)
    try:
        with open(config_file, "r") as f:
            return json.load(f)
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
    return re.sub(r'[\\/*?:"<>|]', "", s)

def get_video_title(url):
    result = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error retrieving title for video: {url}")
        return None
    return result.stdout.strip()

def download_file(url, format_option, output_template, max_retries):
    command = ["yt-dlp", "-f", format_option, "--continue", "-o", output_template, url]
    for attempt in range(1, max_retries + 1):
        logging.info(f"Attempt {attempt}: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return True, ""
        logging.error(f"Attempt {attempt} failed for {url}: {result.stderr}")
    return False, result.stderr

def merge_files(video_file, audio_file, output_file):
    command = ["ffmpeg", "-i", video_file, "-i", audio_file, "-c:v", "copy", "-c:a", "aac", output_file, "-y"]
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
    
    # Templates for temporary file names
    video_temp = os.path.join(temp_dir, f"{safe_title_str}_video.%(ext)s")
    audio_temp = os.path.join(temp_dir, f"{safe_title_str}_audio.%(ext)s")
    final_output = os.path.join(output_dir, f"{safe_title_str}.{output_format}")
    
    if mode == "both":
        success_video, err_video = download_file(url, "bestvideo", video_temp, max_retries)
        if not success_video:
            logging.error(f"Error downloading video stream for '{safe_title_str}': {err_video}")
            return
        success_audio, err_audio = download_file(url, "bestaudio", audio_temp, max_retries)
        if not success_audio:
            logging.error(f"Error downloading audio stream for '{safe_title_str}': {err_audio}")
            return

        # Find downloaded files (extensions are determined by yt-dlp)
        video_file, audio_file = None, None
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
        logging.info(f"Successfully merged and saved: {final_output}")
        try:
            os.remove(video_file)
            os.remove(audio_file)
        except Exception as e:
            logging.error(f"Error cleaning up temporary files for '{safe_title_str}': {e}")
    
    elif mode == "audio":
        success_audio, err_audio = download_file(url, "bestaudio", audio_temp, max_retries)
        if not success_audio:
            logging.error(f"Error downloading audio stream for '{safe_title_str}': {err_audio}")
            return
        for file in os.listdir(temp_dir):
            if file.startswith(f"{safe_title_str}_audio."):
                try:
                    os.rename(os.path.join(temp_dir, file), final_output)
                    logging.info(f"Audio saved: {final_output}")
                except Exception as e:
                    logging.error(f"Error moving audio file for '{safe_title_str}': {e}")
                break

    elif mode == "video":
        success_video, err_video = download_file(url, "bestvideo", video_temp, max_retries)
        if not success_video:
            logging.error(f"Error downloading video stream for '{safe_title_str}': {err_video}")
            return
        for file in os.listdir(temp_dir):
            if file.startswith(f"{safe_title_str}_video."):
                try:
                    os.rename(os.path.join(temp_dir, file), final_output)
                    logging.info(f"Video saved: {final_output}")
                except Exception as e:
                    logging.error(f"Error moving video file for '{safe_title_str}': {e}")
                break
    else:
        logging.error(f"Unknown mode: {mode}")

def main():
    config = load_config()

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

    extract_command = ["yt-dlp", "--flat-playlist", "--print", "url", playlist_url]
    result = subprocess.run(extract_command, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Error extracting playlist: {result.stderr}")
        sys.exit(1)
    video_urls = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    total_videos = len(video_urls)
    if total_videos == 0:
        logging.error("No videos found in the playlist.")
        sys.exit(1)

    start = config.get("start", 1)
    end = config.get("end", total_videos)
    if end == 0:
        end = total_videos
    if start < 1 or end > total_videos or start > end:
        logging.error("Invalid range specified. Ensure 1 <= start <= end <= total videos in playlist.")
        sys.exit(1)
    
    selected_urls = video_urls[start-1:end]
    total_selected = len(selected_urls)
    logging.info(f"Found {total_videos} videos in the playlist. Downloading videos {start} to {end} ({total_selected} videos).")
    
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
    logging.basicConfig(level=logging.INFO)
    logging.info("Disclaimer: Use this tool only for lawful purposes in accordance with YouTube's terms of service.")
    main()
