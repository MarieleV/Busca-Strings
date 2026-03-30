# index.html se comunica com o servidor via fetch/JSON.

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, request, jsonify, send_from_directory
from controller import run_search, run_all, get_algorithm_info

app = Flask(__name__, static_folder=".")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/algorithms")
def algorithms():
    return jsonify(get_algorithm_info())


@app.route("/api/search", methods=["POST"])
def search():
    data = request.json or {}
    text      = data.get("text", "")
    pattern   = data.get("pattern", "")
    algorithm = data.get("algorithm", "naive")
    result = run_search(algorithm, text, pattern)
    return jsonify(result)


@app.route("/api/compare", methods=["POST"])
def compare():
    data    = request.json or {}
    text    = data.get("text", "")
    pattern = data.get("pattern", "")
    results = run_all(text, pattern)
    return jsonify(results)


if __name__ == "__main__":
    print("▶  String Search Lab  →  http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
