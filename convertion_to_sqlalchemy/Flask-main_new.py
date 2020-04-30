from flask import Flask, request, render_template, redirect
from models_backpack_inventory_profile import AllItemsBackpack, AllItemsInventory, Profile
from session import session_creator
import base64
from sqlalchemy import asc

app = Flask(__name__, template_folder="templates", static_folder="static")
global_id = None


@app.route("/")
@app.route("/error")
def main_menu():
    global global_id
    global_id = None
    context = {}
    if request.path == "/error":
        context["error"] = "Błąd logowania"
    return render_template("index.html", **context)


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
        context["message"] = "Poprawnie dodano do armi!"
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
        try:
            id_result = session.query(Profile) \
                .filter(Profile.login == login) \
                .filter(Profile.password == password) \
                .one()
        except Exception:
            return redirect("/error")
        global_id = id_result.id
    result = session.query(Profile) \
        .filter(Profile.id == global_id) \
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
               "capacity": result.capacity,
               "money": result.money}
    if result.inventory:
        context["inventory"] = [
            (base64.b64encode(element.item_data.image).decode("utf-8"), element.name, element.item_data.modifier) for
            element in result.inventory]
    if result.backpack:
        context["backpack"] = [(base64.b64encode(element.item_data.image).decode("utf-8"), element.name) for element in
                               result.backpack]
    return render_template("profile.html", **context)


@app.route("/shop/<text>")
def shop(text):
    context = {}
    session = session_creator()
    if text == "Weapons":
        result = session.query(AllItemsInventory) \
            .filter(AllItemsInventory.type.in_(["Sword", "Axe", "Dagger", "Mace"]))\
            .order_by(asc(AllItemsInventory.price))\
            .all()
    else:
        result = session.query(AllItemsInventory) \
            .filter(AllItemsInventory.type == text)\
            .order_by(asc(AllItemsInventory.price))\
            .all()
    global global_id
    money_result = session.query(Profile)\
        .filter(Profile.id == global_id)\
        .one()
    context["inventory"] = [
            (base64.b64encode(element.image).decode("utf-8"), element.name, element.modifier, element.price) for
            element in result]
    context["money"] = money_result.money
    return render_template("shop.html", **context)


if __name__ == "__main__":
    app.run(debug=True)

# TODO: jak dodawać bronie? jak zmieniac statystyki(modyfikatory)?
# TODO: sklep dokończyć, kupowanie broni, wypisywanie ich po cenie
# TODO: przedmioty z diablo 3,
# TODO: logger przy błęnym logowaniu
