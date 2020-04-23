from flask import Flask, request, render_template
from models_backpack_inventory_profile import BackpackItem, InventoryItem, Profile
from session import session_creator
import base64

app = Flask(__name__, template_folder="templates", static_folder="static")
global_id = None


@app.route("/")
@app.route("/main")
def main_menu():
    global global_id
    global_id = None
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create_new_champion():
    session = session_creator()
    context = {}
    login = request.form.get("login")
    password = request.form.get("password")
    repeated_password = request.form.get("repeat_password")
    name = request.form.get("hero_name")
    if password == repeated_password and password is not None and repeated_password is not None:
        new_profile = Profile(name=name, login=login, password=password)
        session.add(new_profile)
        session.commit()
        context["message"] = "Poprawnie dodano do bazy! Do boju!"
    elif password != repeated_password:
        context["error"] = "Podane hasła nie są identyczne"
    return render_template("create_hero.html", **context)


@app.route("/profile", methods=["get", "post"])
def profile():
    """
    Endpoint "/profile" operates on 2 methods(post, get): post is provided by login page(index.html) and get is provided
    by menu shortcut(menu.html). When calling this endpoint from shortcut menu, id is taken from global
    variable set after logging in to receive most updated data to populate web page.
    """
    global global_id
    session = session_creator()
    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")
        id_result = session.query(Profile)\
            .filter(Profile.login == login)\
            .filter(Profile.password == password)\
            .one()
        global_id = id_result.id
    result = session.query(Profile)\
        .filter(Profile.id == global_id)\
        .one()
    context = {"name": result.name,
               "level": result.level,
               "exp": result.exp,
               "hp": result.hp,
               "mana": result.mana,
               "stamina": result.stamina,
               "armor": result.armor,
               "attack_dmg": result.attack_dmg,
               "chance_to_crit": result.chance_to_crit,
               "chance_to_steal": result.chance_to_steal,
               "capacity": result.capacity}
    if result.inventory:
        context["inventory"] = [(base64.b64encode(element.item_data.image).decode("utf-8"), element.name) for element in result.inventory]
    if result.backpack:
        context["backpack"] = [(base64.b64encode(element.item_data.image).decode("utf-8"), element.name) for element in result.backpack]
    return render_template("profile.html", **context)
    # TODO: jak dodawać bronie? jak zmieniac statystyki(modyfikatory)?
    # TODO: kasa, sklep


if __name__ == "__main__":
    app.run(debug=True)
