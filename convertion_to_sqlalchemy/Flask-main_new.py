from flask import Flask, request, render_template, redirect
from models_backpack_inventory_profile import AllItemsBackpack, AllItemsInventory, Profile, InventoryItem
from session import session_creator
import base64
from sqlalchemy import asc
import logging

app = Flask(__name__, template_folder="templates", static_folder="static")

formatter = logging.Formatter("%(asctime)s- [%(levelname)s]: %(message)s")
handler = logging.FileHandler('loggs.txt', encoding="utf-8")
handler.setFormatter(formatter)
app.logger.addHandler(handler)

global_id = None


@app.route("/")
@app.route("/error")
def main_menu():
    """
    Main page that includes login area. If user fails to log in there will be logg created in "loggs.txt"
    :return:
    """
    global global_id
    global_id = None
    context = {}
    if request.path == "/error":
        ip = request.remote_addr
        app.logger.error(f"Użytkownik {ip} wprowadził niepoprawne dane logowania")
        context["error"] = "Błąd logowania"
    return render_template("index.html", **context)


@app.route("/create", methods=["GET", "POST"])
def create_new_champion():
    """
    Allows to create new character with passed data.
    :return:
    """
    session = session_creator()
    context = {}
    login = request.form.get("login")
    password = request.form.get("password")
    repeated_password = request.form.get("repeat_password")
    name = request.form.get("hero_name")
    if password and login and name:
        logins_names_list = session.query(Profile).all()
        if login not in [element.login for element in logins_names_list] and name not in [element.login for element in logins_names_list]:
            if password == repeated_password:
                if name in ["Lukasz", "Łukasz"]:
                    new_profile = Profile(name=name, login=login, password=password, attack_dmg=15)
                else:
                    new_profile = Profile(name=name, login=login, password=password)
                session.add(new_profile)
                session.commit()
                context["message"] = "Poprawnie dodano do armi!"
            elif password != repeated_password:
                context["error"] = "Podane hasła nie są identyczne"
        else:
            context["error"] = "Podany login lub nazwa postaci są już zajęte"
    elif password == "" or login == "" or name == "":
        context["error"] = "Pozostawiono puste pola"
    return render_template("create_hero.html", **context)


@app.route("/profile", methods=["get", "post"])
def profile():
    """
    Endpoint "/profile" operates on 2 methods(post, get): post is provided by login page(index.html) and get is provided
    by menu shortcut(menu.html). When calling this endpoint from shortcut menu, id is taken from global
    variable set after logging in to receive most updated data to populate web page. Displays all characters data.
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
            (base64.b64encode(element.item_data.image).decode("utf-8"), element.name, element.item_data.modifier,
             element.item_data.type) for element in result.inventory]
    if result.backpack:
        context["backpack"] = [(base64.b64encode(element.item_data.image).decode("utf-8"), element.name) for element in
                               result.backpack]
    return render_template("profile.html", **context)


def change_statistic(profile_data, modifier, plus=True):
    """
    Takes in profile_data(data from sql of the profile), modifier(statistics that are suppose to be changed and their
    values) and plus= parameter to determine if statistics are being added or removed. Makes requested changes in
    database.
    :return:
    """
    session = session_creator()
    split_modifier = modifier.split(";")
    for data in split_modifier:
        element_component = data.split(" ")
        dictionary = {"attack_dmg": profile_data.attack_dmg,
                      "chance_to_crit": profile_data.chance_to_crit,
                      "hp": profile_data.hp,
                      "mana": profile_data.mana,
                      "stamina": profile_data.stamina,
                      "armor": profile_data.armor,
                      "chance_to_steal": profile_data.chance_to_steal}
        if "." in element_component[0]:
            if plus:
                session.query(Profile) \
                    .filter(Profile.id == global_id) \
                    .update({element_component[1]: dictionary[element_component[1]] + float(element_component[0])})
            else:
                session.query(Profile) \
                    .filter(Profile.id == global_id) \
                    .update({element_component[1]: dictionary[element_component[1]] - float(element_component[0])})
        else:
            if plus:
                session.query(Profile) \
                    .filter(Profile.id == global_id) \
                    .update({element_component[1]: dictionary[element_component[1]] + int(element_component[0])})
            else:
                session.query(Profile) \
                    .filter(Profile.id == global_id) \
                    .update({element_component[1]: dictionary[element_component[1]] - int(element_component[0])})
    session.commit()


@app.route("/shop/<text>", methods=["get", "post"])
def shop(text):
    """
    Takes in text which determines what kind of items are being displayed(default showing 'Weapon'). Allows to add new
    items to inventory or modify currently equiped. After each purchase modifies money amount in database and statistics
    with a use of change_statistics().
    :return:
    """
    context = {}
    session = session_creator()
    result = session.query(AllItemsInventory) \
        .filter(AllItemsInventory.type == text)\
        .order_by(asc(AllItemsInventory.price))\
        .all()
    global global_id
    profile_result = session.query(Profile)\
        .filter(Profile.id == global_id)\
        .one()
    context["inventory"] = [
            (base64.b64encode(element.image).decode("utf-8"), element.name, element.modifier, element.price) for
            element in result]

    new_item_name = request.form.get("item")
    if new_item_name is None:
        pass
    else:
        #zwraca wartości wybranego przedmiotu
        item_result = session.query(AllItemsInventory)\
            .filter(AllItemsInventory.name == new_item_name)\
            .one()
        new_item_price = item_result.price
        new_item_type = item_result.type
        new_item_modifier = item_result.modifier

        #modyfikuje posiadaną kasę i statystyki(usuwa stare statystyki i dodaje nowe)
        budget_result = profile_result.money - new_item_price
        if budget_result < 0:
            context["error"] = "Brak środków"
        else:
            if new_item_type in [element.item_data.type for element in profile_result.inventory]:
                for element in profile_result.inventory:
                    if new_item_type == element.item_data.type:
                        profile_result.money += (element.item_data.price * 0.75)
                        change_statistic(profile_result, element.item_data.modifier, plus=False)
                        element.name = new_item_name
                        session.commit()
                        change_statistic(profile_result, element.item_data.modifier)
            else:
                item = InventoryItem(hero_id=global_id, name=new_item_name)
                session.add(item)
                change_statistic(profile_result, new_item_modifier)
            profile_result.money -= new_item_price
            session.commit()
    context["money"] = profile_result.money
    return render_template("shop.html", **context)


if __name__ == "__main__":
    app.run(debug=True)

# TODO: sklep dokończyć,
# TODO: questy i walka(mapa)
# TODO: backpack
