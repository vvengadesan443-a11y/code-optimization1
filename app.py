from flask import Flask, render_template, request, jsonify
from optimizer import optimize_code

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/optimize", methods=["POST"])
def optimize():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    techniques = payload.get("techniques", ["dag", "peephole"])
    if not isinstance(code, str) or not code.strip():
        return jsonify({"error": "Please enter some code to optimize."}), 400
    try:
        result = optimize_code(code, techniques)
        return jsonify(result)
    except Exception as exc:
        app.logger.exception("Optimization failed")
        return jsonify({"error": f"Could not optimize this input: {exc}"}), 400

if __name__ == "__main__":
    app.run(debug=True)
