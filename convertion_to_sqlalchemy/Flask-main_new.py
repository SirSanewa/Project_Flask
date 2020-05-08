from flask import Flask, request, render_template, redirect, session, url_for
from sqlalchemy.orm.exc import NoResultFound
from models_backpack_inventory_profile import AllItemsBackpack, AllItemsInventory, Profile, InventoryItem, BackpackItem
from session import session_creator
import base64
from sqlalchemy import asc
import logging
from key import secret_key
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = secret_key

formatter = logging.Formatter("%(asctime)s- [%(levelname)s]: %(message)s")
handler = logging.FileHandler('loggs.txt', encoding="utf-8")
handler.setFormatter(formatter)
app.logger.addHandler(handler)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session:
            return view(*args, **kwargs)
        else:
            return redirect('/')

    return wrapped_view


@app.route("/")
@app.route("/error")
def main_menu():
    """
    Main page that includes login area. If user fails to log in there will be logg created in "loggs.txt"
    :return:
    """
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
    session_sql = session_creator()
    context = {}
    login = request.form.get("login")
    password = request.form.get("password")
    repeated_password = request.form.get("repeat_password")
    name = request.form.get("hero_name")
    if password and login and name:
        logins_names_list = session_sql.query(Profile).all()
        if login not in [element.login for element in logins_names_list] and name not in [element.login for element in logins_names_list]:
            if password == repeated_password:
                hashed_password = generate_password_hash(password)
                if any(substring in name for substring in ["Lukasz", "lukasz", "Łukasz", "łukasz"]):
                    new_profile = Profile(name=name, login=login, password=hashed_password, attack_dmg=15, money=150)
                else:
                    new_profile = Profile(name=name, login=login, password=hashed_password)
                session_sql.add(new_profile)
                session_sql.commit()
                context["message"] = "Poprawnie dodano do armi!"
            elif password != repeated_password:
                context["error"] = "Podane hasła nie są identyczne"
        else:
            context["error"] = "Podany login lub nazwa postaci są już zajęte"
    elif password == "" or login == "" or name == "":
        context["error"] = "Pozostawiono puste pola"
    return render_template("create_hero.html", **context)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/check_login", methods=["POST"])
def check_login():
    session_sql = session_creator()
    login = request.form.get("login")
    password = request.form.get("password")
    try:
        profile_result = session_sql.query(Profile) \
            .filter(Profile.login == login) \
            .one()
    except NoResultFound:
        return redirect("/error")
    if profile_result:
        hashed_password = profile_result.password
        if check_password_hash(hashed_password, password):
            session["user_id"] = profile_result.id
            return redirect(url_for("profile"))
        else:
            return redirect(url_for("error"))


@app.route("/profile", methods=["get", "post"])
@login_required
def profile():
    """
    Endpoint "/profile" operates on 2 methods(post, get): post is provided by login page(index.html) and get is provided
    by menu shortcut(menu.html). When calling this endpoint from shortcut menu, id is taken from global
    variable set after logging in to receive most updated data to populate web page. Displays all characters data.
    """
    user_id = session.get("user_id")
    session_sql = session_creator()
    result = session_sql.query(Profile) \
        .filter(Profile.id == user_id) \
        .one()
    context = {"name": result.name,
               "level": result.level,
               "exp": result.exp,
               "hp": result.hp,
               "max_hp": result.max_hp,
               "mana": result.mana,
               "max_mana": result.max_mana,
               "stamina": result.stamina,
               "max_stamina": result.max_stamina,
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
        context["backpack"] = [
            (base64.b64encode(element.item_data.image).decode("utf-8"), element.name, element.item_data.modifier)
            for element in result.backpack]
    return render_template("profile.html", **context)


def change_statistic(profile_data, modifier, plus=True):
    """
    Takes in profile_data(data from sql of the profile), modifier(statistics that are suppose to be changed and their
    values) and plus= parameter to determine if statistics are being added or removed. Makes requested changes in
    database.
    """
    user_id = session.get("user_id")
    session_sql = session_creator()
    dictionary = {"attack_dmg": [("attack_dmg", profile_data.attack_dmg)],
                  "chance_to_crit": [("chance_to_crit", profile_data.chance_to_crit)],
                  "max_hp": [("max_hp", profile_data.max_hp), ("hp", profile_data.hp)],
                  "max_mana": [("max_mana", profile_data.max_mana), ("mana", profile_data.mana)],
                  "max_stamina": [("max_stamina", profile_data.max_stamina), ("stamina", profile_data.stamina)],
                  "armor": [("armor", profile_data.armor)],
                  "chance_to_steal": [("chance_to_steal", profile_data.chance_to_steal)],
                  "hp": [("hp", profile_data.hp)],
                  "mana": [("mana", profile_data.mana)]}
    split_modifier = modifier.split(";")
    for data in split_modifier:
        element_component = data.split(" ")
        for item in dictionary[element_component[1]]:
            # dodac nazwy statystyk, stworzyć mniejsze funkcje
            if item[0] in ["chance_to_crit", "chance_to_steal"]:
                if plus:
                    my_dict = {item[0]: item[1] + float(element_component[0])}
                else:
                    my_dict = {item[0]: item[1] - float(element_component[0])}
            else:
                if plus:
                    my_dict = {item[0]: item[1] + int(element_component[0])}
                else:
                    my_dict = {item[0]: item[1] - int(element_component[0])}
            session_sql.query(Profile)\
                .filter(Profile.id == user_id)\
                .update(my_dict)

        if profile_data.hp > profile_data.max_hp:
            profile_data.hp = profile_data.max_hp
        if profile_data.mana > profile_data.max_mana:
            profile_data.mana = profile_data.max_mana
    session_sql.commit()


@app.route("/shop/<text>", methods=["get", "post"])
@login_required
def shop(text):
    """
    Takes in text which determines what kind of items are being displayed(default showing 'Weapon'). Allows to add new
    items to inventory or modify currently equiped. After each purchase modifies money amount in database and statistics
    with a use of change_statistics().
    :return:
    """
    context = {}
    session_sql = session_creator()
    user_id = session.get("user_id")
    if text == "Consumable":
        result = session_sql.query(AllItemsBackpack) \
            .filter(AllItemsBackpack.type == text) \
            .order_by(asc(AllItemsBackpack.price)) \
            .all()
    else:
        result = session_sql.query(AllItemsInventory) \
            .filter(AllItemsInventory.type == text)\
            .order_by(asc(AllItemsInventory.price))\
            .all()
    profile_result = session_sql.query(Profile)\
        .filter(Profile.id == user_id)\
        .one()
    context["inventory"] = [
            (base64.b64encode(element.image).decode("utf-8"), element.name, element.modifier, element.price,
             element.type) for element in result]

    # print(request.form.get("item"), type(request.form.get("item")))
    if request.form.get("item"):
        new_item = request.form.get("item")
        item_details = new_item.split(",")
        new_item_name = item_details[0]
        new_item_type = item_details[1]
        print(f"type: {new_item_type}, name: {new_item_name}")

        if new_item_type == "Consumable":
            item_result = session_sql.query(AllItemsBackpack) \
                .filter(AllItemsBackpack.name == new_item_name) \
                .one()
            new_item_price = item_result.price

            # modyfikuje posiadaną kasę i statystyki(usuwa stare statystyki i dodaje nowe)
            budget_result = profile_result.money - new_item_price
            if budget_result < 0:
                context["error"] = "Brak środków"
            else:
                if profile_result.capacity > 1:
                    item = BackpackItem(hero_id=user_id, name=new_item_name)
                    session_sql.add(item)
        else:
            #zwraca wartości wybranego przedmiotu
            item_result = session_sql.query(AllItemsInventory)\
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
                            # TODO: dodać funckję replace_item
                            profile_result.money += (element.item_data.price * 0.75)
                            change_statistic(profile_result, element.item_data.modifier, plus=False)
                            element.name = new_item_name
                            session_sql.commit()
                            change_statistic(profile_result, element.item_data.modifier)
                else:
                    item = InventoryItem(hero_id=user_id, name=new_item_name)
                    session_sql.add(item)
                    change_statistic(profile_result, new_item_modifier)
        profile_result.money -= new_item_price
        session_sql.commit()
    context["money"] = profile_result.money
    return render_template("shop.html", **context)


if __name__ == "__main__":
    app.run(debug=True)

# TODO: sklep dokończyć,
# TODO: questy i walka(mapa)
# TODO: backpack
# TODO: wielkość potionów w sklepie
