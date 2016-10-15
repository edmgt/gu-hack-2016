#! venv/bin/python
from flask import Flask, render_template
from controllers import report
app = Flask(__name__)


@app.route("/")
def index():
    ctx = report()
    return render_template("index.html", **ctx)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
