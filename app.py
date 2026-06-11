import os
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from visualizer import main as build_graph
from analyzer import heatmap, numerical_stats_table
from graph_utils import two_variable


app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
ALLOWED_EXTENSIONS = {"csv"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_file():
    """Save the CSV and return the stored filename."""
    if "file" not in request.files:
        return jsonify({"error": "No file in the request"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Only .csv files are allowed"}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(input_path)

    return jsonify({"filename": filename})


@app.route("/visualize", methods=["POST"])
def visualize():
    """Build the network graph for a previously uploaded file."""
    body = request.get_json(silent=True)
    if not body or "filename" not in body:
        return jsonify({"error": "No filename provided"}), 400

    filename = body["filename"]
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(input_path):
        return jsonify({"error": "File not found on server"}), 404

    output_name = f"{os.path.splitext(filename)[0]}_graph.html"
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_name)
    build_graph(input_path, output_path)

    return jsonify({"graph_url": f"/outputs/{output_name}"})


@app.route("/analyze", methods=["POST"])
def analyze():

    # error checking and shtuff
    body = request.get_json(silent=True)
    if not body or "filename" not in body:
        return jsonify({"error": "No filename provided"}), 400
    
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], body["filename"])
    if not os.path.exists(input_path):
        return jsonify({"error": "File not found on server"}), 404

    # use the backend. upload to frontend. shtuff.
    correlation_matrix, heatmap_columns, heatmap_values = heatmap(input_path)
    stats_matrix, stats_columns, stats_values = numerical_stats_table(input_path)
    print(stats_columns)

    # prepare for JavaScript!!!
    return jsonify({
        "heatmapColumns": heatmap_columns, 
        "heatmapValues": heatmap_values,
        "statsColumns": stats_columns,
        "statsValues": stats_values,
    })


@app.route("/plot", methods=["POST"])
def plot_two_variables():
    """return Plotly scatterplot for two variables."""

    # again, error checking
    body = request.get_json(silent=True)
    if not body or not all(k in body for k in ("filename", "x", "y")):
        return jsonify({"error": "Filename and two variables are required"}), 400
    
    input_path = os.path.join(app.config["UPLOAD_FOLDER"], body["filename"])
    if not os.path.exists(input_path):
        return jsonify({"error": "File not found on server"}), 404
    
    # uploads and analysis! yay!
    x_col = body["x"]
    y_col = body["y"]
    x_col, y_col, count, figure = two_variable(input_path, x_col, y_col)

    # prepare for WAR!!!!!
    return jsonify({
        "x": x_col,
        "y": y_col,
        "count": int(count),
        "figure": figure,
    })


@app.route("/outputs/<path:filename>")
def serve_output(filename):
    return send_from_directory(app.config["OUTPUT_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True)
