from flask import Flask, request, jsonify, redirect
from urllib.parse import urlparse

import redis
import threading

from collections import defaultdict

from key_gen import generate_secure_unique_key
from data_helpers import (
    get_url_record,
    get_url_record,
    insert_record,
    check_connection,
    pull_url_analytics,
    update_url_access_analytics,
)

app = Flask(__name__)

redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)


@app.route("/")
def index():
    return "Hello from Flask!"


@app.route("/<short_key>", methods=["GET"])
def redirect_short_url(short_key):

    long_url = redis_client.get(short_key)
    if not long_url:
        long_url = get_url_record(short_key)
        if not long_url:
            return jsonify(error="Short URL does not exist"), 404

    threading.Thread(target=update_url_access_analytics, args=(short_key,)).start()

    return redirect(long_url, code=301)


def is_valid_url(url):
    result = urlparse(url)
    return all([result.scheme, result.netloc])


@app.route("/analytics/<short_url>", methods=["GET"])
def get_analytics(short_url):
    result = pull_url_analytics(short_url)
    return jsonify(result), 200


@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json()

    if not data or "long_url" not in data:
        return jsonify({"error": "Missing required fields: long_url"}), 400

    # Get values from post body
    long_url = data["long_url"]

    if not is_valid_url(long_url):
        return jsonify({"error": "Invalid URL"}), 400

    short_key = data.get("back_half")
    if short_key:
        if get_url_record(short_key):
            return jsonify({"error": "Custom key already in use"}), 409
    else:
        short_key = generate_short_key(long_url, None)
        # Check if URL hash already exists, otherwise keep creating
        while get_url_record(short_key):
            # simple solution, consider improving
            short_key = generate_short_key(long_url)

    # Store URL mapping
    res = insert_record(short_key, long_url)
    if not res:
        return jsonify({"error": "Sorry something went wrong"}), 500
    redis_client.set(short_key, long_url)
    api_domain = request.host_url
    short_url = f"{api_domain}{short_key}"
    return jsonify(short_url=short_url), 200


def generate_short_key(long_url, back_half=None):
    # Generate a hash of the long URL to use as the short URL key
    return back_half if back_half else generate_secure_unique_key()


def get_longer_url(short_url):
    long_url = get_url_record(short_url)
    if long_url:
        return long_url
    else:
        return None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
