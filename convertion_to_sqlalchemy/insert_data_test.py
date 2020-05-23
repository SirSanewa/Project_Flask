from models_backpack_inventory_profile import AllItemsInventory, AllItemsBackpack, Monster
import os
from session import session_creator

session = session_creator()

items = []

directory = "static/items_inventory"
for file in os.listdir(directory):
    with open(f"{directory}/{file}", "rb") as f:
        byte_file = bytearray(f.read())
        file_name = file.split("|")
        item_elements = file_name[0].split(",")
        item_name = item_elements[0]
        modifier = item_elements[1]
        split_modifier = modifier.split(";")
        dictionary = {"attack_dmg": None, "chance_to_crit": None, "max_hp": None, "max_mana": None,
                      "max_stamina": None, "armor": None, "chance_to_steal": None}
        for statistic in split_modifier:
            stat_component = statistic.split(" ")
            value = stat_component[0]
            stat_name = stat_component[1]
            dictionary[stat_name] = value
        price = item_elements[2]
        item_type = item_name.split("_")[1]
        if item_type in ["Axe", "Mace", "Sword", "Dagger"]:
            item_type = "Weapon"
        items.append(AllItemsInventory(**dictionary,
                                       image=byte_file,
                                       name=item_name,
                                       price=price,
                                       type=item_type))

directory = "static/items_backpack"
for file in os.listdir(directory):
    with open(f"{directory}/{file}", "rb") as f:
        byte_file = bytearray(f.read())
        file_name = file.split("|")
        item_elements = file_name[0].split(",")
        item_name = item_elements[0]
        modifier = item_elements[1]
        split_modifier = modifier.split(";")
        dictionary = {"attack_dmg": None, "chance_to_crit": None, "max_hp": None, "max_mana": None,
                      "max_stamina": None, "armor": None, "chance_to_steal": None, "hp": None, "mana": None}
        for statistic in split_modifier:
            stat_component = statistic.split(" ")
            value = stat_component[0]
            stat_name = stat_component[1]
            dictionary[stat_name] = value
        price = item_elements[2]
        item_type = "Consumable"
        items.append(AllItemsBackpack(**dictionary, image=byte_file, name=item_name, price=price, type=item_type))


directory = "static/monsters"
for file in os.listdir(directory):
    with open(f"{directory}/{file}", "rb") as f:
        byte_file = bytearray(f.read())
        file_name = file.split("|")
        item_elements = file_name[0].split(",")
        item_name = item_elements[0]
        statistics = item_elements[1]
        reward = item_elements[2]
        money_reward = int(reward.split(" ")[0])
        exp_reward = int(reward.split(" ")[1])
        split_statistics = statistics.split(";")
        dictionary = {"attack_dmg": None, "chance_to_crit": None, "hp": None, "mana": None,
                      "stamina": None, "armor": None, "level": None}
        for element in split_statistics:
            stat_component = element.split(" ")
            value = stat_component[0]
            stat_name = stat_component[1]
            dictionary[stat_name] = value
        items.append(Monster(**dictionary,
                             image=byte_file,
                             name=item_name,
                             max_hp=dictionary["hp"],
                             max_mana=dictionary["mana"],
                             max_stamina=dictionary["stamina"],
                             money_reward=money_reward,
                             exp_reward=exp_reward))

session.bulk_save_objects(items)
session.commit()
