# YouTube Playlist Downloader

![YouTube Playlist Downloader](https://socialify.git.ci/king04aman/youtube-playlist-downloader/image?description=1&font=Jost&language=1&logo=https%3A%2F%2Fimages.weserv.nl%2F%3Furl%3Dhttps%3A%2F%2Favatars.githubusercontent.com%2Fu%2F62813940%3Fv%3D4%26h%3D250%26w%3D250%26fit%3Dcover%26mask%3Dcircle%26maxage%3D7d&name=1&owner=1&pattern=Floating%20Cogs&theme=Dark)

YouTube Playlist Downloader is a robust and efficient tool for downloading videos from YouTube playlists. Designed for users who need to retrieve multiple videos in the best available quality, this tool downloads video and audio streams separately, merges them using FFmpeg, and supports automatic retries, parallel downloads, and configurable download ranges—all driven through a simple `config.json` file.

## Features

- **Automated Downloading:**  
  Downloads all videos from a YouTube playlist using the best available quality streams.

- **Configurable Download Range:**  
  Specify which videos in a playlist to download (e.g., only videos 3 to 8).

- **Multiple Download Modes:**  
  Choose to download both video and audio (merged), or only audio, or only video.

- **Automatic Merging:**  
  Uses FFmpeg to seamlessly merge video and audio streams into a single file.

- **Retry Mechanism:**  
  Implements automatic retries for failed downloads to handle intermittent network issues.

- **Parallel Downloads:**  
  Supports multi-threaded downloading to reduce total download time.

- **Config File Driven:**  
  All settings (playlist URL, output directory, download range, etc.) are managed via a `config.json` file for ease of use.

- **Detailed Logging & Progress Tracking:**  
  Logs all actions and errors to a log file while displaying progress via a terminal progress bar.

## Prerequisites

Before using this tool, ensure the following are installed on your system:

- **Python 3.6+**
- **yt-dlp:**  
  Install via pip:  
  ```bash
  pip install yt-dlp
  ```
- **FFmpeg:**  
  Ensure FFmpeg is installed and available in your system's PATH. Download from [FFmpeg Official Site](https://ffmpeg.org/download.html).
- **tqdm:**  
  Install via pip:  
  ```bash
  pip install tqdm
  ```

## Installation

Clone this repository to your local machine:

```bash
git clone https://github.com/king04aman/YouTube-Playlist-Downloader.git
cd YouTube-Playlist-Downloader
```

## Configuration

This tool is entirely driven by a configuration file. Create a `config.json` file in the root directory of the project. Below is an example configuration:

```json
{
    "playlist_url": "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID",
    "output": "downloads",
    "parallel": 2,
    "start": 1,
    "end": 0,
    "output_format": "mp4",
    "mode": "both",
    "retries": 3
}
```

- **playlist_url:** Full URL of the YouTube playlist.
- **output:** Directory where downloaded videos will be saved.
- **parallel:** Number of parallel downloads.
- **start:** 1-based index of the first video to download.
- **end:** 1-based index of the last video to download (set to `0` to download until the end).
- **output_format:** Desired container format (e.g., `mp4`, `mkv`, `webm`).
- **mode:** Download mode - `"both"` (video + audio), `"audio"`, or `"video"`.
- **retries:** Maximum number of retry attempts for each download.

If the `config.json` file is not found, the tool will exit with an error and instruct you to generate it.

## Usage

Run the script using Python:

```bash
python main.py
```

The script will read the configuration from `config.json`, extract the video URLs from the provided playlist, and download the videos according to the specified settings.

## Contributing

Contributions to the YouTube Playlist Downloader project are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes with clear commit messages.
4. Push to your fork and submit a pull request.
5. Follow any guidelines outlined in our [CONTRIBUTING.md](CONTRIBUTING.md) file.

## YouTube Disclaimer

**Disclaimer:**  
This tool is provided solely for downloading content for which you have the legal rights to do so. Use this software in compliance with YouTube's Terms of Service and for lawful purposes only. The developers assume no responsibility for any misuse of this tool. Please ensure that you respect copyright and distribution laws when using this software.

## Contact

If you have any questions or need further assistance, please feel free to reach out or open an issue in the repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

### Happy Downloading! 🎉🎉

