import unittest
from unittest.mock import patch, MagicMock
import os
import sys

from main import safe_filename, get_video_title, download_file, merge_files

class TestYouTubePlaylistDownloader(unittest.TestCase):
    
    def test_safe_filename(self):
        # Test that unsafe characters are removed correctly
        test_str = "Invalid/Name:Test*File?"
        expected = "InvalidNameTestFile"
        self.assertEqual(safe_filename(test_str), expected)

    @patch('downloader.subprocess.run')
    def test_get_video_title_success(self, mock_run):
        # Simulate successful retrieval of video title
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout = "Test Video Title\n"
        mock_run.return_value = process_mock
        
        title = get_video_title("dummy_url")
        self.assertEqual(title, "Test Video Title")
    
    @patch('downloader.subprocess.run')
    def test_get_video_title_failure(self, mock_run):
        # Simulate failure to retrieve title
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.stderr = "Error occurred"
        mock_run.return_value = process_mock
        
        title = get_video_title("dummy_url")
        self.assertIsNone(title)
    
    @patch('downloader.subprocess.run')
    def test_download_file_success(self, mock_run):
        # Simulate a successful download (return code 0 on first attempt)
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stderr = ""
        mock_run.return_value = process_mock
        
        success, err = download_file("dummy_url", "bestvideo", "template", max_retries=3)
        self.assertTrue(success)
        self.assertEqual(err, "")
    
    @patch('downloader.subprocess.run')
    def test_download_file_failure(self, mock_run):
        # Simulate failure on all attempts
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.stderr = "Download error"
        mock_run.return_value = process_mock
        
        success, err = download_file("dummy_url", "bestvideo", "template", max_retries=2)
        self.assertFalse(success)
        self.assertEqual(err, "Download error")
    
    @patch('downloader.subprocess.run')
    def test_merge_files_success(self, mock_run):
        # Simulate successful merging with FFmpeg
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stderr = ""
        mock_run.return_value = process_mock
        
        success, err = merge_files("video.mp4", "audio.m4a", "output.mp4")
        self.assertTrue(success)
        self.assertEqual(err, "")
    
    @patch('downloader.subprocess.run')
    def test_merge_files_failure(self, mock_run):
        # Simulate merge failure via FFmpeg
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.stderr = "Merge error"
        mock_run.return_value = process_mock
        
        success, err = merge_files("video.mp4", "audio.m4a", "output.mp4")
        self.assertFalse(success)
        self.assertEqual(err, "Merge error")

if __name__ == '__main__':
    unittest.main()
