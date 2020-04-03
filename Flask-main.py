from flask import Flask, request, render_template

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
@app.route("/main")
def main_menu():
    return render_template("index.html")


@app.route("/profile")
def profile():
    name = request.args.get("name")
    context = {"name": name}
    return render_template("profile.html", **context)


if __name__ == "__main__":
    app.run(debug=True)
