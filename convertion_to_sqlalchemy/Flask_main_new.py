from datetime import datetime
from flask import Flask, request, render_template, redirect, session, url_for
from sqlalchemy.orm.exc import NoResultFound
from models_backpack_inventory_profile import AllItemsBackpack, AllItemsInventory, Profile, InventoryItem, BackpackItem, Quests
from session import session_creator
import base64
from sqlalchemy import asc, inspect
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
SALE_RATIO = 0.7


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session:
            return view(*args, **kwargs)
        else:
            return redirect('/')

    return wrapped_view


def object_as_dict(obj):
    return {item.key: getattr(obj, item.key)
            for item in inspect(obj).mapper.column_attrs}


def create_modifier(dictionary):
    item_modifier = ""
    for item in dictionary:
        if item in ["chance_to_crit", "chance_to_steal", "armor", "max_hp", "max_mana", "max_stamina", "attack_dmg",
                    "hp", "mana"]:
            if dictionary[item] is not None:
                item_modifier += "+" + str(dictionary[item]) + " " + item + " "
    return item_modifier


def create_inventory_for_profile(database):
    item_list = []
    for element in database:
        dictionary = object_as_dict(element.item_data)
        item_modifier = create_modifier(dictionary)
        item_list.append((base64.b64encode(element.item_data.image).decode("utf-8"), element.name, item_modifier, element.item_data.type))
    return item_list


def create_backpack_for_profile(database):
    item_list = []
    for element in database:
        dictionary = object_as_dict(element.item_data)
        item_modifier = create_modifier(dictionary)
        item_list.append((base64.b64encode(element.item_data.image).decode("utf-8"), element.name, item_modifier, element.amount))
    return item_list


def create_inventory_for_shop(database):
    item_list = []
    for element in database:
        dictionary = object_as_dict(element)
        item_modifier = create_modifier(dictionary)
        item_list.append((base64.b64encode(element.image).decode("utf-8"), element.name, item_modifier, element.type, element.price))
    return item_list


def change_statistic(profile_data, item_data, plus=True):
    """
    Takes in profile_data(data from sql of the profile), modifier(statistics that are suppose to be changed and their
    values) and plus= parameter to determine if statistics are being added or removed. Makes requested changes in
    database.
    """
    changable_statistics = ["chance_to_crit", "chance_to_steal","armor", "max_hp", "max_mana", "max_stamina",
                            "attack_dmg", "hp", "mana"]
    dual_stats = ["max_hp", "max_mana", "max_stamina"]
    user_id = session.get("user_id")
    session_sql = session_creator()
    dictionary_item = object_as_dict(item_data)
    dictionary_profile = object_as_dict(profile_data)
    for statistic in dictionary_item:
        if statistic in changable_statistics:
            item_statistic_modifier = dictionary_item[statistic]
            if item_statistic_modifier is not None:
                current_profile_statistic_value = dictionary_profile[statistic]
                if plus:
                    my_dict = {statistic: current_profile_statistic_value + item_statistic_modifier}
                else:
                    my_dict = {statistic: current_profile_statistic_value - item_statistic_modifier}
                if statistic in dual_stats:
                    duel_stats_update(session_sql, statistic, dictionary_profile, dictionary_item, plus)
                session_sql.query(Profile) \
                    .filter(Profile.id == user_id) \
                    .update(my_dict)
    session_sql.commit()


def duel_stats_update(session_sql, statistic, dictionary_profile, dictionary_item, plus):
    user_id = session.get("user_id")
    dual_statistics = {"max_hp": "hp", "max_mana": "mana", "max_stamina": "stamina"}
    mod_statistic = dual_statistics[statistic]
    current_profile_statistic_value = dictionary_profile[dual_statistics[statistic]]
    modifier_value = dictionary_item[statistic]
    if plus:
        dual_dict = {mod_statistic: current_profile_statistic_value + modifier_value}
    else:
        dual_dict = {mod_statistic: current_profile_statistic_value - modifier_value}
    session_sql.query(Profile) \
        .filter(Profile.id == user_id) \
        .update(dual_dict)
    session_sql.commit()


def add_consumable(session_sql, profile_result, user_id, new_item_name):
    item_result = session_sql.query(AllItemsBackpack) \
        .filter(AllItemsBackpack.name == new_item_name) \
        .one()
    new_item_price = item_result.price
    budget_result = profile_result.money - new_item_price
    if budget_result < 0:
        return "Brak środków"
    else:
        if new_item_name in [item.name for item in profile_result.backpack]:
            current_item = session_sql.query(BackpackItem)\
                .filter(BackpackItem.name == new_item_name)\
                .filter(BackpackItem.hero_id == user_id)\
                .one()
            current_item.amount += 1
        else:
            if profile_result.capacity > 0:
                item = BackpackItem(hero_id=user_id, name=new_item_name, amount=1)
                profile_result.capacity -= 1
                session_sql.add(item)
            else:
                return "Nie masz wystarczająco miejsca w plecaku"
    profile_result.money -= new_item_price
    session_sql.commit()


def replace_item(profile_result, element, new_item_name, session_sql):
    global SALE_RATIO
    profile_result.money += (element.item_data.price * SALE_RATIO)
    change_statistic(profile_result, element.item_data, plus=False)
    element.name = new_item_name
    session_sql.commit()
    change_statistic(profile_result, element.item_data)


def add_inventory_item(session_sql, new_item_name, profile_result, user_id):
    # zwraca wartości nowego przedmiotu
    item_result = session_sql.query(AllItemsInventory) \
        .filter(AllItemsInventory.name == new_item_name) \
        .one()
    new_item_price = item_result.price
    new_item_type = item_result.type
    # modyfikuje posiadaną kasę i statystyki(usuwa stare statystyki i dodaje nowe)
    budget_result = profile_result.money - new_item_price
    if budget_result < 0:
        return "Brak środków"
    else:
        if new_item_type in [element.item_data.type for element in profile_result.inventory]:
            for element in profile_result.inventory:
                if new_item_type == element.item_data.type:
                    replace_item(profile_result, element, new_item_name, session_sql)
        else:
            item = InventoryItem(hero_id=user_id, name=new_item_name)
            session_sql.add(item)
            change_statistic(profile_result, item_result)
    profile_result.money -= new_item_price
    session_sql.commit()


def create_quests_for_new_character(login, hashed_password, session_sql):
    profile = session_sql.query(Profile) \
        .filter(Profile.login == login) \
        .filter(Profile.password == hashed_password) \
        .one()
    quests = Quests(hero_id=profile.id)
    session_sql.add(quests)
    session_sql.commit()


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
        logins_and_names_list = session_sql.query(Profile).all()
        if login not in [element.login for element in logins_and_names_list] and name not in [element.login for element in logins_and_names_list]:
            if password == repeated_password:
                hashed_password = generate_password_hash(password)
                if any(substring in name for substring in ["Lukasz", "lukasz", "Łukasz", "łukasz"]):
                    new_profile = Profile(name=name, login=login, password=hashed_password, attack_dmg=15, money=150)
                else:
                    new_profile = Profile(name=name, login=login, password=hashed_password)
                session_sql.add(new_profile)
                session_sql.commit()
                create_quests_for_new_character(login, hashed_password, session_sql)
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
            return redirect("/error")


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
               "max_lvl_exp": int(result.level * 1.5 * 100),
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
        context["inventory"] = create_inventory_for_profile(result.inventory)
    if result.backpack:
        context["backpack"] = create_backpack_for_profile(result.backpack)
    if request.form.get("use_item"):
        used_item_name = request.form.get("use_item")
        use_consumable(used_item_name, result, session_sql, user_id)
        return redirect("/profile")
    elif request.form.get("sell_item"):
        sold_item = request.form.get("sell_item")
        sell_consumable(sold_item, result, session_sql, user_id)
        return redirect("/profile")
    return render_template("profile.html", **context)


def sell_consumable(item_name, profile_result, session_sql, user_id):
    item = session_sql.query(BackpackItem)\
        .filter(BackpackItem.name == item_name)\
        .filter(BackpackItem.hero_id == user_id)\
        .one()
    global SALE_RATIO
    profile_result.money += item.item_data.price * SALE_RATIO
    item.amount -= 1
    if item.amount == 0:
        session_sql.query(BackpackItem) \
            .filter(BackpackItem.name == item_name) \
            .filter(BackpackItem.hero_id == user_id) \
            .delete()
        profile_result.capacity += 1
    session_sql.commit()


def use_consumable(item_name, profile_result, session_sql, user_id):
    changable_statistics = {"hp": "max_hp", "mana": "max_mana", "stamina": "max_stamina"}
    item = session_sql.query(BackpackItem)\
        .filter(BackpackItem.name == item_name)\
        .filter(BackpackItem.hero_id == user_id)\
        .one()
    dictionary_item_description = object_as_dict(item.item_data)
    dictionary_profile = object_as_dict(profile_result)
    if item.amount > 0:
        for statistic in dictionary_item_description:
            statistic_value = dictionary_item_description[statistic]
            if statistic in changable_statistics and statistic_value is not None:
                current_profile_statistic_value = dictionary_profile[statistic]
                max_profile_statistic_value = dictionary_profile[changable_statistics[statistic]]
                if current_profile_statistic_value < max_profile_statistic_value:
                    item_statistic_modifier = dictionary_item_description[statistic]
                    if current_profile_statistic_value + item_statistic_modifier <= max_profile_statistic_value:
                        my_dict = {statistic: current_profile_statistic_value + item_statistic_modifier}
                    else:
                        my_dict = {statistic: max_profile_statistic_value}
                    item.amount -= 1
                    if item.amount == 0:
                        session_sql.query(BackpackItem)\
                            .filter(BackpackItem.name == item_name)\
                            .filter(BackpackItem.hero_id == user_id)\
                            .delete()
                        profile_result.capacity += 1
                    session_sql.query(Profile) \
                        .filter(Profile.id == user_id) \
                        .update(my_dict)
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
    context["inventory"] = create_inventory_for_shop(result)
    # jeśli zostanie wskazany przedmiot do kupienia
    if request.form.get("item"):
        new_item = request.form.get("item")
        item_details = new_item.split(",")
        new_item_name = item_details[0]
        new_item_type = item_details[1]
        if new_item_type == "Consumable":
            if add_consumable(session_sql, profile_result, user_id, new_item_name):
                context["error"] = add_consumable(session_sql, profile_result, user_id, new_item_name)
        else:
            if add_inventory_item(session_sql, new_item_name, profile_result, user_id):
                context["error"] = add_inventory_item(session_sql, new_item_name, profile_result, user_id)
    context["money"] = profile_result.money
    return render_template("shop.html", **context)


@app.route("/quests")
@login_required
def quests():
    user_id = session.get("user_id")
    session_sql = session_creator()
    profile = session_sql.query(Profile) \
        .filter(Profile.id == user_id) \
        .one()
    time_now = datetime.now()
    quest_time = datetime(2020, 5, 28, 23, 59, 59)
    context = {"time": quest_time,
               "quest_1": quest_details_buy_simple_axe(session_sql, profile),
               "quest_2": quest_details_buy_shield(session_sql, profile)}
    if time_now < quest_time:
        pass
    return render_template("quests.html", **context)


def quest_details_buy_shield(session_sql, profile):
    quest_item_type = "Shield"
    money_reward = 25
    exp_reward = 50
    quest_details = {"reward": f"${money_reward}, {exp_reward}exp"}
    if not profile.quests.quest_2:
        if quest_item_type in [item.item_data.type for item in profile.inventory]:
            profile.quests.quest_2 = True
            profile.money += money_reward
            update_exp_and_lvl(exp_reward, profile)
            session_sql.commit()
            quest_details["completed"] = True
        else:
            quest_details["completed"] = False
    else:
        quest_details["completed"] = True
    return quest_details


def update_exp_and_lvl(exp_reward, profile):
    profile.exp += exp_reward
    max_exp = int(profile.level * 1.5 * 100)
    if profile.exp > max_exp:
        profile.exp -= max_exp
        profile.level += 1


def quest_details_buy_simple_axe(session_sql, profile):
    quest_item = "Simple_Axe"
    money_reward = 25
    exp_reward = 30
    item = session_sql.query(AllItemsInventory) \
        .filter(AllItemsInventory.name == quest_item) \
        .one()
    quest_details = {"image": base64.b64encode(item.image).decode("utf-8"),
                     "name": item.name,
                     "reward": f"${money_reward}, {exp_reward}exp"}
    if not profile.quests.quest_1:
        if quest_item in [item.name for item in profile.inventory]:
            profile.quests.quest_1 = True
            profile.money += money_reward
            update_exp_and_lvl(exp_reward, profile)
            session_sql.commit()
            quest_details["completed"] = True
    else:
        quest_details["completed"] = True
    return quest_details


if __name__ == "__main__":
    app.run(debug=True)

# TODO: walka(mapa)
# TODO: sprobować porobić testy
# TODO: questy tygodnidowe
