import io
import os
import re
import urllib.request
import logging
from flask import Flask, request, jsonify, Response, stream_with_context
from pytube import YouTube, exceptions as pytube_exceptions

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def is_valid_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+(&\S*)?$"
    return re.match(pattern, url) is not None

def get_video_info(url):
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
        logging.error("Error getting video info: %s", e)
        return None, str(e)

def get_video_stream(url):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        if stream:
            # Adding User-Agent to request headers
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            return stream
        else:
            return None
    except pytube_exceptions.PytubeError as e:
        logging.error("Error getting video stream: %s", e)
        return None

@app.after_request
def add_accept_origin(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400

    video_info, error = get_video_info(url)
    if error:
        return jsonify({"error": error}), 500

    stream = get_video_stream(url)
    if not stream:
        return jsonify({"error": "Stream not found."}), 500

    def generate():
        try:
            response = urllib.request.urlopen(stream.url)
            while True:
                chunk = response.read(4096)
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            logging.error("Error streaming video: %s", e)
            yield b''

    response = Response(stream_with_context(generate()), mimetype='video/mp4')
    response.headers.set(
        "Content-Disposition", 
        f"attachment; filename={video_info['title']}.mp4"
    )
    return response



@app.route('/video_info', methods=['POST'])
def video_info():
    data = request.get_json()
    url = data.get('url')

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400
    
    video_info, error_message = get_video_info(url)
    if video_info:
        return jsonify(video_info), 200
    else:
        return jsonify({"error": error_message}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
