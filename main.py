import argparse
import io
import os
import sys
import threading
import time
from flask import Flask, request, jsonify, Response
from pytube import YouTube, exceptions as pytube_exceptions
import re

class YouTubeDownloader:
    def __init__(self):
        self.app = Flask(__name__)
        
    def run(self):
        print("Starting server...")
        
        self._setup_routes()
        self.flask_thread = threading.Thread(target=self._run_flast, daemon=True)
        self.flask_thread.start()
        
        while 1:
            time.sleep(1)

        
    def _is_valid_youtube_url(self, url):
        pattern = r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+(&\S*)?$"
        return re.match(pattern, url) is not None

    def _get_video_info(self, url):
        try:
            yt = YouTube(url)
            yt.streams.first()
            video_info = {
                "title": yt.title,
                "author": yt.author,
                "length": yt.length,
                "views": yt.views,
                "description": yt.description,
                "publish_date": yt.publish_date,
            }
            return video_info, None
        except Exception as e:
            return None, str(e)

    def _get_video_stream(self, url):
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
            if stream:
                video_bytes = io.BytesIO()
                stream.stream_to_buffer(video_bytes)
                video_bytes.seek(0)
                return video_bytes
            else:
                return None
        except pytube_exceptions.PytubeError:
            return None

    def _setup_routes(self):
        @self.app.after_request
        def add_accept_origin(request):
            request.headers["Access-Control-Allow-Origin"] = "*"
            request.headers["Access-Control-Allow-Headers"] = "*"
            return request
        
        @self.app.route('/download', methods=['POST'])
        def download():
            """
            Endpoint for downloading a video based on the provided URL.
            Retrieves video information and streams the video in response.
            Returns the video file as an attachment with the appropriate filename.
            """
            data = request.get_json()
            url = data.get('url')
            if not self._is_valid_youtube_url(url):
                return jsonify({"error": "Invalid YouTube URL."}), 400

            video_info, error = self._get_video_info(url)
            if error:
                return jsonify({"error": error}), 500

            stream = self._get_video_stream(url)
            if not stream:
                return jsonify({"error": "Stream not found."}), 500

            response = Response(stream, mimetype='video/mp4')
            response.headers.set(
                "Content-Disposition", 
                f"attachment; filename={video_info['title']}.mp4"
            )
            return response
        
        @self.app.route('/video_info', methods=['POST'])
        def video_info():
            """
            Endpoint for retrieving video information.

            This route handles a POST request to '/video_info' and expects a JSON payload with a 'url' field.
            The function validates the provided YouTube URL using the `_is_valid_youtube_url` method.
            If the URL is valid, it calls the `_get_video_info` method to retrieve video information.
            If the video information is successfully retrieved, it returns a JSON response with the video information and a status code of 200.
            If there is an error retrieving the video information, it returns a JSON response with an error message and a status code of 500.

            Parameters:
            - None

            Returns:
            - If the YouTube URL is invalid:
                - A JSON response with an error message and a status code of 400.
            - If the video information is successfully retrieved:
                - A JSON response with the video information and a status code of 200.
            - If there is an error retrieving the video information:
                - A JSON response with an error message and a status code of 500.
            """
            data = request.get_json()
            url = data.get('url')

            if not self._is_valid_youtube_url(url):
                return jsonify({"error": "Invalid YouTube URL."}), 400
            
            video_info, error_message = self._get_video_info(url)
            if video_info:
                return jsonify(video_info), 200
            else:
                return jsonify({"error": error_message}), 500

    def _run_flast(self):
        """
        Runs the Flask application on a specified port.

        This function parses command line arguments using the `argparse` module to determine the TCP port to listen on. If no port is specified, it defaults to the value of the `PORT` environment variable or 5000.

        The Flask application is then run on all available network interfaces (`"0.0.0.0"`) on the specified port.

        If there is an exception during the execution of the Flask application, the function flushes the standard output and error streams and exits the process with a status code of 1.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        parser = argparse.ArgumentParser(description="YouTube Downloader")
        parser.add_argument(
            "-p",
            "--port",
            type=int,
            default=os.getenv("PORT", 5000),
            help=" TCP Port to listen to."
        )
        args = parser.parse_args()
        
        try:
            self.app.run(host="0.0.0.0", port=args.port, threaded=True)
        except:
            sys.stdout.flush()
            sys.stderr.flush()
            os._exit(1)
            raise

    def stop(self):
        """
        This method is intentionally left empty.
        """
        pass

def main():
    testapp = YouTubeDownloader()

    try:
        testapp.run()
    except Exception as e:
        print(f"Error: {e}")
        testapp.stop()

if __name__ == "__main__":
    main()