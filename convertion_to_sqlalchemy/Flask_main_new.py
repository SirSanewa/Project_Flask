from datetime import datetime
from random import choice, randint
from flask import Flask, request, render_template, redirect, session, url_for
from sqlalchemy.orm.exc import NoResultFound
from models_backpack_inventory_profile import AllItemsBackpack, AllItemsInventory, Profile, InventoryItem, \
    BackpackItem, Quests, Monster
from session import session_creator
import base64
from sqlalchemy import asc, inspect
import logging
from key import secret_key
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps


app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = secret_key
session_sql = session_creator()

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


def define_user_id_and_sql_profile():
    global session_sql
    user_id = session.get("user_id")
    profile_result = session_sql.query(Profile) \
        .filter(Profile.id == user_id) \
        .one()
    return user_id, profile_result


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
        item_list.append((base64.b64encode(element.item_data.image).decode("utf-8"), element.name, item_modifier,
                          element.item_data.type))
    return item_list


def create_backpack_for_profile(database):
    item_list = []
    for element in database:
        dictionary = object_as_dict(element.item_data)
        item_modifier = create_modifier(dictionary)
        item_list.append(
            (base64.b64encode(element.item_data.image).decode("utf-8"), element.name, item_modifier, element.amount))
    return item_list


def create_inventory_for_shop(database):
    item_list = []
    for element in database:
        dictionary = object_as_dict(element)
        item_modifier = create_modifier(dictionary)
        item_list.append(
            (base64.b64encode(element.image).decode("utf-8"), element.name, item_modifier, element.type, element.price))
    return item_list


def change_statistic(profile_data, item_data, plus=True):
    """
    Takes in profile_data(data from sql of the profile), modifier(statistics that are suppose to be changed and their
    values) and plus= parameter to determine if statistics are being added or removed. Makes requested changes in
    database.
    """
    global session_sql
    changeable_statistic = ["chance_to_crit", "chance_to_steal", "armor", "max_hp", "max_mana", "max_stamina",
                            "attack_dmg", "hp", "mana"]
    dual_stats = ["max_hp", "max_mana", "max_stamina"]
    user_id = session.get("user_id")
    dictionary_item = object_as_dict(item_data)
    dictionary_profile = object_as_dict(profile_data)
    for statistic in dictionary_item:
        if statistic in changeable_statistic:
            item_statistic_modifier = dictionary_item[statistic]
            if item_statistic_modifier is not None:
                current_profile_statistic_value = dictionary_profile[statistic]
                if plus:
                    my_dict = {statistic: current_profile_statistic_value + item_statistic_modifier}
                else:
                    my_dict = {statistic: current_profile_statistic_value - item_statistic_modifier}
                if statistic in dual_stats:
                    duel_stats_update(statistic, dictionary_profile, dictionary_item, plus)
                session_sql.query(Profile) \
                    .filter(Profile.id == user_id) \
                    .update(my_dict)
    session_sql.commit()


def duel_stats_update(statistic, dictionary_profile, dictionary_item, plus):
    global session_sql
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


def add_consumable(profile_result, user_id, new_item_name):
    global session_sql
    item_result = session_sql.query(AllItemsBackpack) \
        .filter(AllItemsBackpack.name == new_item_name) \
        .one()
    new_item_price = item_result.price
    budget_result = profile_result.money - new_item_price
    if budget_result < 0:
        return "Brak środków"
    else:
        if new_item_name in [item.name for item in profile_result.backpack]:
            current_item = session_sql.query(BackpackItem) \
                .filter(BackpackItem.name == new_item_name) \
                .filter(BackpackItem.hero_id == user_id) \
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


def replace_item(profile_result, element, new_item_name):
    global session_sql
    global SALE_RATIO
    profile_result.money += (element.item_data.price * SALE_RATIO)
    change_statistic(profile_result, element.item_data, plus=False)
    element.name = new_item_name
    session_sql.commit()
    change_statistic(profile_result, element.item_data)


def add_inventory_item(new_item_name, profile_result, user_id):
    global session_sql
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
                    replace_item(profile_result, element, new_item_name)
        else:
            item = InventoryItem(hero_id=user_id, name=new_item_name)
            session_sql.add(item)
            change_statistic(profile_result, item_result)
    profile_result.money -= new_item_price
    session_sql.commit()


def create_quests_for_new_character(login, hashed_password):
    global session_sql
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
    global session_sql
    context = {}
    login = request.form.get("login")
    password = request.form.get("password")
    repeated_password = request.form.get("repeat_password")
    name = request.form.get("hero_name")
    if password and login and name:
        logins_and_names_list = session_sql.query(Profile).all()
        if login not in [element.login for element in logins_and_names_list] and name not in [element.login for element
                                                                                              in logins_and_names_list]:
            if password == repeated_password:
                hashed_password = generate_password_hash(password)
                if any(substring in name for substring in ["Lukasz", "lukasz", "Łukasz", "łukasz"]):
                    new_profile = Profile(name=name, login=login, password=hashed_password, attack_dmg=15, money=150)
                else:
                    new_profile = Profile(name=name, login=login, password=hashed_password)
                session_sql.add(new_profile)
                session_sql.commit()
                create_quests_for_new_character(login, hashed_password)
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
    global session_sql
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
    global session_sql
    user_id, profile_result = define_user_id_and_sql_profile()
    context = {"name": profile_result.name,
               "level": profile_result.level,
               "exp": profile_result.exp,
               "max_lvl_exp": int(profile_result.level * 1.5 * 100),
               "hp": profile_result.hp,
               "max_hp": profile_result.max_hp,
               "mana": profile_result.mana,
               "max_mana": profile_result.max_mana,
               "stamina": profile_result.stamina,
               "max_stamina": profile_result.max_stamina,
               "armor": profile_result.armor,
               "attack_dmg": profile_result.attack_dmg,
               "chance_to_crit": profile_result.chance_to_crit,
               "chance_to_steal": profile_result.chance_to_steal,
               "capacity": profile_result.capacity,
               "money": round(profile_result.money, 2)}
    if profile_result.inventory:
        context["inventory"] = create_inventory_for_profile(profile_result.inventory)
    if profile_result.backpack:
        context["backpack"] = create_backpack_for_profile(profile_result.backpack)
    if request.form.get("use_item"):
        used_item_name = request.form.get("use_item")
        use_consumable(used_item_name, profile_result)
        return redirect("/profile")
    elif request.form.get("sell_item"):
        sold_item = request.form.get("sell_item")
        sell_consumable(sold_item, profile_result, user_id)
        return redirect("/profile")
    return render_template("profile.html", **context)


def sell_consumable(item_name, profile_result, user_id):
    global session_sql
    item = session_sql.query(BackpackItem) \
        .filter(BackpackItem.name == item_name) \
        .filter(BackpackItem.hero_id == user_id) \
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


def use_consumable(item_name, profile_result):
    global session_sql
    changable_statistics = {"hp": "max_hp", "mana": "max_mana", "stamina": "max_stamina"}
    other_statistics = ["attack_dmg"]
    item = session_sql.query(BackpackItem) \
        .filter(BackpackItem.name == item_name) \
        .filter(BackpackItem.hero_id == profile_result.id) \
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
                    session_sql.query(Profile) \
                        .filter(Profile.id == profile_result.id) \
                        .update(my_dict)
                    item.amount -= 1
                    if item.amount == 0:
                        session_sql.query(BackpackItem) \
                            .filter(BackpackItem.name == item_name) \
                            .filter(BackpackItem.hero_id == profile_result.id) \
                            .delete()
                        profile_result.capacity += 1
            elif statistic in other_statistics and statistic_value is not None:
                current_profile_statistic_value = dictionary_profile[statistic]
                item_statistic_modifier = dictionary_item_description[statistic]
                my_dict = {statistic: current_profile_statistic_value + item_statistic_modifier}
                session_sql.query(Profile) \
                    .filter(Profile.id == profile_result.id) \
                    .update(my_dict)
                item.amount -= 1
                if item.amount == 0:
                    session_sql.query(BackpackItem) \
                        .filter(BackpackItem.name == item_name) \
                        .filter(BackpackItem.hero_id == profile_result.id) \
                        .delete()
                    profile_result.capacity += 1
        session_sql.commit()
        return f"Użyto {item_name.replace('_', ' ')}"


@app.route("/shop/<text>", methods=["get", "post"])
@login_required
def shop(text):
    """
    Takes in text which determines what kind of items are being displayed(default showing 'Weapon'). Allows to add new
    items to inventory or modify currently equiped. After each purchase modifies money amount in database and statistics
    with a use of change_statistics().
    :return:
    """
    global session_sql
    context = {}
    user_id, profile_result = define_user_id_and_sql_profile()
    if text == "Consumable":
        result = session_sql.query(AllItemsBackpack) \
            .filter(AllItemsBackpack.type == text) \
            .order_by(asc(AllItemsBackpack.price)) \
            .all()
    else:
        result = session_sql.query(AllItemsInventory) \
            .filter(AllItemsInventory.type == text) \
            .order_by(asc(AllItemsInventory.price)) \
            .all()
    context["inventory"] = create_inventory_for_shop(result)
    # jeśli zostanie wskazany przedmiot do kupienia
    if request.form.get("item"):
        new_item = request.form.get("item")
        item_details = new_item.split(",")
        new_item_name = item_details[0]
        new_item_type = item_details[1]
        if new_item_type == "Consumable":
            if add_consumable(profile_result, user_id, new_item_name):
                context["error"] = add_consumable(profile_result, user_id, new_item_name)
        else:
            if add_inventory_item(new_item_name, profile_result, user_id):
                context["error"] = add_inventory_item(new_item_name, profile_result, user_id)
    context["money"] = round(profile_result.money, 2)
    return render_template("shop.html", **context)


@app.route("/quests")
@login_required
def quests():
    global session_sql
    _, profile_result = define_user_id_and_sql_profile()
    time_now = datetime.now()
    quest_time = datetime(2020, 5, 28, 23, 59, 59)
    context = {"time": quest_time,
               "quest_1": quest_details_buy_simple_axe(profile_result),
               "quest_2": quest_details_buy_shield(profile_result)}
    if time_now < quest_time:
        pass
    return render_template("quests.html", **context)


def quest_details_buy_shield(profile):
    global session_sql
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


def update_exp_and_lvl(exp_reward, profile, win_fight=True):
    level_update_modifier = 0.05
    max_exp = int(profile.level * 1.5 * 100)
    if win_fight:
        profile.exp += exp_reward
        while profile.exp >= max_exp:
            profile.exp -= max_exp
            profile.level += 1
            profile.max_hp += profile.max_hp * level_update_modifier
            profile.hp += profile.hp * level_update_modifier
            profile.max_mana += profile.max_mana * level_update_modifier
            profile.mana += profile.mana * level_update_modifier
            profile.attack_dmg += profile.attack_dmg * level_update_modifier
            profile.armor += profile.armor * level_update_modifier
    if not win_fight:
        if profile.exp - exp_reward >= 0:
            profile.exp -= exp_reward
        else:
            if profile.level > 1:
                profile.exp += int((profile.level-1) * 1.5 * 100)
                profile.exp -= exp_reward
                profile.level -= 1
                profile.max_hp = round((profile.max_hp * 100)/((level_update_modifier*100)+100))
                profile.hp = round((profile.hp * 100) / ((level_update_modifier * 100) + 100))
                profile.max_mana = round((profile.max_mana * 100)/((level_update_modifier*100)+100))
                profile.mana = round((profile.mana * 100) / ((level_update_modifier * 100) + 100))
                profile.attack_dmg = round((profile.attack_dmg * 100)/((level_update_modifier*100)+100))
                profile.armor = round((profile.armor * 100) / ((level_update_modifier * 100) + 100))
            else:
                profile.exp = 0


def quest_details_buy_simple_axe(profile):
    global session_sql
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


@app.route("/journey")
@login_required
def journey():
    global session_sql
    _, profile_result = define_user_id_and_sql_profile()
    return render_template("journey.html", level=profile_result.level)


@app.route("/searching/<location>", methods=["post", "get"])
@login_required
def searching(location):
    global session_sql
    _, profile_result = define_user_id_and_sql_profile()
    monster_list = {"forest": ["Warewolf", "Goblin", "Ent", "Centaur"],
                    "sea": None,
                    "dessert": None,
                    "graveyard": None}
    monster_choosen = choice(monster_list[location])
    monster = session_sql.query(Monster)\
        .filter(Monster.name == monster_choosen)\
        .one()
    update_monster_level(monster, profile_result, set_default=False)
    return redirect(url_for("search_area", location=location, monster=monster_choosen))


def update_monster_level(monster, profile_result, set_default=False):
    global session_sql
    level_update_modifier =0.05
    if not set_default:
        new_monster_level = randint(1, profile_result.id + 2)
        if new_monster_level >= 2:
            monster.level = new_monster_level
            for _ in range(1, new_monster_level):
                monster.hp += monster.hp * level_update_modifier
                monster.max_hp += monster.max_hp * level_update_modifier
                monster.mana += monster.mana * level_update_modifier
                monster.max_mana += monster.max_mana * level_update_modifier
                monster.attack_dmg += monster.attack_dmg * level_update_modifier
                monster.armor += monster.armor * level_update_modifier
    if set_default:
        if monster.level >= 2:
            for _ in range(1, monster.level):
                monster.level -= 1
                monster.max_hp = (monster.max_hp * 100)/((level_update_modifier*100)+100)
                monster.hp = (monster.hp * 100) / ((level_update_modifier * 100) + 100)
                monster.max_mana = (monster.max_mana * 100) / ((level_update_modifier * 100) + 100)
                monster.mana = (monster.mana * 100) / ((level_update_modifier * 100) + 100)
                monster.attack_dmg = (monster.attack_dmg * 100) / ((level_update_modifier * 100) + 100)
                monster.armor = (monster.armor * 100) / ((level_update_modifier * 100) + 100)
    session_sql.commit()


@app.route("/search_area/", methods=["get", "post"])
@login_required
def search_area():
    global session_sql
    your_move = None
    enemy_move = None
    money_lost_modifier = 0.1
    location = request.args["location"]
    monster_name = request.args["monster"]
    monster = session_sql.query(Monster) \
        .filter(Monster.name == monster_name) \
        .one()
    _, profile_result = define_user_id_and_sql_profile()
    hero_spell_cost = 40
    hero_spell_dmg = round(40 + (40 * ((profile_result.level - 1) * 0.02)))
    context = {"location": location,
               "monster": monster,
               "monster_image": base64.b64encode(monster.image).decode("utf-8"),
               "profile": profile_result,
               "spell_cost": hero_spell_cost,
               "spell_dmg": hero_spell_dmg}
    if profile_result.hp > 0 and monster.hp > 0:
        if request.form.get("attack"):
            your_move = attack(profile_result, monster)
        elif request.form.get("spell"):
            your_move = spell(profile_result, monster, hero_spell_cost, hero_spell_dmg)
        elif request.form.get("list"):
            used_item_name = request.form.get("list")
            your_move = use_consumable(used_item_name, profile_result)
        elif request.form.get("run"):
            money_lost = profile_result.money * money_lost_modifier
            profile_result.money -= round(money_lost, 2)
            update_monster_level(monster, profile_result, set_default=True)
            reset_monster_stats(monster)
            session_sql.commit()
            return render_template("fight_result.html", result="run", money=round(money_lost, 2))
        if request.form:
            enemy_move = monster_attack(monster, profile_result)
        context["your_move"] = your_move
        context["enemy_move"] = enemy_move
        if profile_result.hp < 0:
            update_monster_level(monster, profile_result, set_default=True)
            reset_monster_stats(monster)
            profile_result.hp = 1
            update_exp_and_lvl(monster.exp_reward, profile_result, win_fight=False)
            session_sql.commit()
            return render_template("fight_result.html", result="lost", exp=monster.exp_reward)
        elif monster.hp < 0:
            profile_result.money += monster.money_reward
            update_exp_and_lvl(monster.exp_reward, profile_result)
            update_monster_level(monster, profile_result, set_default=True)
            reset_monster_stats(monster)
            session_sql.commit()
            return render_template("fight_result.html",
                                   result="win",
                                   money_reward=monster.money_reward,
                                   exp_reward=monster.exp_reward)
    return render_template("fight_location.html", **context)


def reset_monster_stats(monster):
    monster.hp = monster.max_hp
    monster.mana = monster.max_mana


def attack(profile_result, monster):
    global session_sql
    crit_dmg_multiplier = 2
    crit_chance = int(profile_result.chance_to_crit * 100)
    chance_to_crit_result = randint(1, 100)
    dmg = int(profile_result.attack_dmg - (monster.armor / 10))
    if chance_to_crit_result <= crit_chance:
        new_dmg = dmg * crit_dmg_multiplier
        monster.hp -= new_dmg
        session_sql.commit()
        return f"Zadałeś {new_dmg} obrażeń krytycznych przeciwnikowi"
    else:
        if_hit_chance = 80
        if_hit_result = randint(1, 100)
        if if_hit_result > if_hit_chance:
            return f"Chybiłeś atak wręcz"
        else:
            monster.hp -= dmg
            session_sql.commit()
            return f"Zadałeś {dmg} obrażeń przeciwnikowi"


def spell(profile_result, monster, hero_spell_cost, hero_spell_dmg):
    global session_sql
    if_hit_chance = 60
    if_hit_result = randint(1, 100)
    if profile_result.mana >= hero_spell_cost:
        profile_result.mana -= hero_spell_cost
        if if_hit_result <= if_hit_chance:
            monster.hp -= hero_spell_dmg
            session_sql.commit()
            return f"Wykonałeś atak magiczny i zadałeś {hero_spell_dmg} dmg obrażeń"
        else:
            return f"Chybiłeś atak magiczny"


def monster_attack(monster, profile_result):
    global session_sql
    _spell_cost = 40
    _spell_dmg = round(40 + (40 * ((monster.level - 1) * 0.02)))
    magic_attack_chance = 40
    crit_dmg_multiplier = 2.5
    result = randint(1, 100)
    if result <= magic_attack_chance and monster.mana > _spell_cost:
        if_hit_chance = 80
        if_hit_result = randint(1, 100)
        monster.mana -= _spell_cost
        if if_hit_result <= if_hit_chance:
            profile_result.hp -= _spell_dmg
            session_sql.commit()
            return f"{monster.name} wykonał atak magiczny i zadał {_spell_dmg} dmg obrażeń"
        else:
            return f"{monster.name} chybił atak magiczny"
    else:
        crit_chance = int(monster.chance_to_crit * 100)
        chance_to_crit_result = randint(1, 100)
        dmg = round(monster.attack_dmg - (profile_result.armor / 10))
        if chance_to_crit_result <= crit_chance:
            new_dmg = dmg * crit_dmg_multiplier
            profile_result.hp -= new_dmg
            session_sql.commit()
            return f"{monster.name} zaatakował i zadał {new_dmg} krytycznych obrażeń"
        else:
            if_hit_chance = 80
            if_hit_result = randint(1, 100)
            if if_hit_result > if_hit_chance:
                return f"{monster.name} chybił atak wręcz"
            else:
                profile_result.hp -= dmg
                session_sql.commit()
                return f"{monster.name} zaatakował i zadał {dmg} obrażeń"


if __name__ == "__main__":
    app.run(debug=True)

# TODO: szpital(leczenie kosztuje energie?)
