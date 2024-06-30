import io
import os
import re
from flask import Flask, request, jsonify, Response
from pytube import YouTube, exceptions as pytube_exceptions

app = Flask(__name__)

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
        return None, str(e)

def get_video_stream(url):
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

    response = Response(stream, mimetype='video/mp4')
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
