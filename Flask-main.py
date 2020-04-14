from flask import Flask, request, render_template
from thief import Thief
import sqlite3

app = Flask(__name__, template_folder="templates", static_folder="static")

global_login = None
global_password = None


@app.route("/")
@app.route("/main")
def main_menu():
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create_new_champion():
    context = {}
    login = request.form.get("login")
    password = request.form.get("password")
    repeated_password = request.form.get("repeat_password")
    name = request.form.get("hero_name")
    if password == repeated_password and password is not None and repeated_password is not None:
        Thief(name, login, password)
    elif password != repeated_password:
        context["error"] = "Wprowadzono błędne hasła"
    return render_template("create_hero.html", **context)


def return_profile(login, password):
    sql_connection = sqlite3.connect("database.db")
    cursor = sql_connection.cursor()
    query = """
    SELECT "id","name", "level", "exp", "hp", "mana", "stamina", "armor", "attack dmg", "chance to crit", "chance to steal", "capacity"
    FROM "profile"
    WHERE login = :login AND password = :password;
    """
    dictionary = {"login": login, "password": password}
    cursor.execute(query, dictionary)
    profile_data = cursor.fetchone()
    sql_connection.commit()
    sql_connection.close()
    return profile_data


def return_backpack(id_number):
    connection = sqlite3.connect("database.db")
    connection.execute("PRAGMA foreign_keys = 1;")
    cursor = connection.cursor()
    query = """
    SELECT b.name AS "item", b.type AS "type", b.amount AS "amount"
    FROM profile as p
    JOIN backpack as b ON p.id = b.hero_id
    WHERE p.id = ?;
    """
    hero_id = str(id_number)
    cursor.execute(query, (hero_id,))
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return result


def return_inventory(id_number):
    connection = sqlite3.connect("database.db")
    connection.execute("PRAGMA foreign_keys = 1;")
    cursor = connection.cursor()
    query = """
    SELECT i.name AS "item", i.type AS "type", i.modifier AS "modifier"
    FROM profile as p
    JOIN inventory as i ON p.id = i.hero_id
    WHERE p.id = ? AND i.type IS NOT NULL;
    """
    hero_id = str(id_number)
    cursor.execute(query, (hero_id,))
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    return result


@app.route("/profile", methods=["get", "post"])
def profile():
    """
    Endpoint "/profile" operates on 2 methods(post, get): post is provided by login page(index.html) and get is provided
    by menu shortcut(menu.html). When calling this endpoint from shortcut menu, login and password are taken from global
    variables set after logging in and passed to return_profile() to receive most updated data to populate web page.
    """
    global global_login
    global global_password
    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")
        profile = return_profile(login, password)
        global_login = login
        global_password = password
    else:
        profile = return_profile(global_login, global_password)
    hero_id, name, level, exp, hp, mana, stamina, armor, attack_dmg, chance_to_crit, chance_to_steal, capacity = profile
    context = {"name": name,
               "level": level,
               "exp": exp,
               "hp": hp,
               "mana": mana,
               "stamina": stamina,
               "armor": armor,
               "attack_dmg": attack_dmg,
               "chance_to_crit": chance_to_crit,
               "chance_to_steal": chance_to_steal,
               "capacity": capacity}
    if return_backpack(hero_id):
        context.update({"backpack": return_backpack(hero_id)})
    if return_inventory(hero_id):
        context.update({"inventory": return_inventory(hero_id)})
    return render_template("profile.html", **context)
    # TODO: zmodyfikować system dodwania przemdiotów do bazy (nie będzie podanych instancji klasy, pozbyć się klas?)
    #  TODO: stworzyć baze danych przedmiotów?, zrobić 2 oddzielne joiny na plecak i sprzęt dla łatwości drukowania
    #   na stronie?


if __name__ == "__main__":
    app.run(debug=True)
