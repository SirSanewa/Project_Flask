import sqlite3
from os import path
from backpack import Inventory


def return_hero_id(hero_name):
    sql_connection = sqlite3.connect("database.db")
    cursor = sql_connection.cursor()
    query = """
    SELECT id FROM "profile"
    WHERE name = ?;
    """
    name = hero_name
    cursor.execute(query, (name,))
    hero_id, = cursor.fetchone()
    sql_connection.commit()
    sql_connection.close()
    return hero_id


class Hero:
    """
    This is a template for Heroes' classes
    """

    def create_profile_in_database(self):
        sql_connection = sqlite3.connect("database.db")
        sql_connection.execute("PRAGMA foreign_keys = ON;")
        cursor = sql_connection.cursor()
        file_path = path.realpath("queries/profile_create_table.sql")
        with open(file_path, encoding="utf-8") as file:
            query_create = file.read()

        file_path_2 = path.realpath("queries/profile_insert_values_default.sql")
        with open(file_path_2, encoding="utf-8") as file:
            query_insert = file.read()

        dictionary = {"name": getattr(self, "hero_name"),
                      "login": getattr(self, "login"),
                      "password": getattr(self, "password"),
                      "hp": getattr(self, "hp"),
                      "mana": getattr(self, "mana"),
                      "stamina": getattr(self, "stamina"),
                      "armor": getattr(self, "armor"),
                      "attack_dmg": getattr(self, "attack_dmg"),
                      "chance_to_crit": getattr(self, "chance_to_crit"),
                      "chance_to_steal": getattr(self, "chance_to_steal"),
                      "capacity": getattr(self, "capacity")
                      }
        cursor.execute(query_create)
        cursor.execute(query_insert, dictionary)
        sql_connection.commit()
        sql_connection.close()

    def __init__(self, hero_name, login, password, hp, mana, stamina, armor, attack_dmg, chance_to_steal, chance_to_crit, capacity):
        self.hero_name = hero_name
        self.login = login
        self.password = password
        self.hp = hp
        self.mana = mana
        self.stamina = stamina
        self.armor = armor
        self.attack_dmg = attack_dmg
        self.chance_to_steal = chance_to_steal
        self.chance_to_crit = chance_to_crit
        self.capacity = capacity
        self.create_profile_in_database()
        hero_id = return_hero_id(self.hero_name)
        self.backpack = Inventory(self.capacity, hero_id)

    def __str__(self):
        return f"{self.hero_name}'s statistics: \n" \
               f"\t-{self.hp} HP, \n" \
               f"\t-{self.mana} mana, \n" \
               f"\t-{self.stamina} stamina,\n" \
               f"\t-{self.armor} armor,\n" \
               f"\t-{self.attack_dmg} attack damage,\n" \
               f"\t-{self.chance_to_steal}% chance to steal\n" \
               f"\t-{self.chance_to_crit}% chance to deal critical damage\n" \
               f"\t-{self.capacity} capacity"

    def __lt__(self, other):
        if self.hp > other.hp:
            return False
        return True

    def add_item(self, item_name, item_type, modifier_amount):
        self.backpack.add_new_item(item_name, item_type, modifier_amount)
        if isinstance(modifier_amount, str):
            modifier_list = modifier_amount.split(", ")
            for element in modifier_list:
                value, statistic = element.split(" ")
                statistic_dict = {"hp": "self.hp",
                                  "mana": "self.mana",
                                  "stamina": "self.stamina",
                                  "armor": "self.armor",
                                  "attack_dmg": "self.attack_dmg",
                                  "chance_to_steal": "self.chance_to_steal",
                                  "chance_to_crit": "self.chance_to_crit",
                                  "capacity": "self.capacity"}
                if value[0] == "+":
                    setattr(self, statistic, eval(statistic_dict[statistic]) + int(value[1:]))
                else:
                    setattr(self, statistic, eval(statistic_dict[statistic]) - int(value[1:]))


if __name__ == "__main__":
    hero = Hero("Aukasz", 1, 1, 1, 1, 1, 1, 1, 1)
    print(hero)

