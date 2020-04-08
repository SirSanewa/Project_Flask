from flask import Flask, request, render_template
from thief import Thief

app = Flask(__name__, template_folder="templates", static_folder="static")


@app.route("/")
@app.route("/main")
def main_menu():
    return render_template("index.html")


@app.route("/create", methods=["get", "post"])
def create_new_champion():
    context = {}
    login = request.form.get("login")
    password = request.form.get("password")
    repeated_password = request.form.get("repeat_password")
    name = request.form.get("hero_name")
    if password == repeated_password and password is not None and repeated_password is not None:
        thief = Thief(name, login, password)
    elif password != repeated_password:
        context["error"] = "Wprowadzono błędne hasła"
    return render_template("create_hero.html", **context)
    #TODO: logowanie postaci

@app.route("/profile")
def profile():
    name = request.args.get("name")
    context = {"name": name}
    return render_template("profile.html", **context)


if __name__ == "__main__":
    app.run(debug=True)
