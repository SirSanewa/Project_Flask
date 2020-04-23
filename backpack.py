import sqlite3
from os import path


def create_database_sqlite(hero_id):
    """
    function creates database in database.db file at first launch of the program, at every next launch just checks if
    the database is in place and do nothing if database already exists.
    """
    sql_connection = sqlite3.connect("database.db")
    sql_connection.execute("PRAGMA foreign_keys = 1;")
    cursor = sql_connection.cursor()
    file_path = path.realpath("queries/backpack_create_database.sql")
    with open(file_path, encoding="utf-8") as file:
        query_create_tables = file.read()
    cursor.executescript(query_create_tables)
    query_insert_values = """
    INSERT INTO "inventory"
    VALUES  (:hero_id, "Helmet", NULL, NULL),
            (:hero_id, "Armor", NULL, NULL),
            (:hero_id, "Gloves", NULL, NULL),
            (:hero_id, "Boots", NULL, NULL),
            (:hero_id, "Weapon", NULL, NULL)
    """
    dictionary = {"hero_id": hero_id}
    cursor.execute(query_insert_values, dictionary)
    sql_connection.commit()
    sql_connection.close()


def insert_data_to_database(item_name, hero_id, item_type, modifier_amount):
    """
    Takes in item_name, item_type, modifier_amount values and creates item in 'backpack' list in database file.
    Initiates create_database_sqlite() to check if database exists or to create it if not.
    """
    sql_connection = sqlite3.connect("database.db")
    cursor = sql_connection.cursor()
    file_path = path.realpath("queries/backpack_insert_data.sql")
    with open(file_path, encoding="utf-8") as file:
        query = file.read()
    dictionary = {"name": item_name, "type": item_type, "amount": modifier_amount, "hero_id": hero_id}
    cursor.execute(query, dictionary)
    sql_connection.commit()
    sql_connection.close()


def return_rows_from_database(table_name, hero_id, readable_names=False):
    """
    Takes in table_name and returns tuples list of every element in the table. If readable_names=False(default) the
    function will return class items_backpack which allows itering over them, if readable_name=True return human readable
    tuple lists. Initiates create_database_sqlite() to check if database exists or to create it if not.
    """
    sql_connection = sqlite3.connect("database.db")
    if not readable_names:
        sql_connection.row_factory = sqlite3.Row
    cursor = sql_connection.cursor()
    query = """
    SELECT * FROM {}
    WHERE hero_id = ?;
    """.format(table_name)
    heros_id = hero_id
    cursor.execute(query, (heros_id,))
    inventory_rows = cursor.fetchall()

    sql_connection.commit()
    sql_connection.close()
    return inventory_rows


def return_amount_from_database_item(item_name, hero_id):
    """
    Takes in item_name and returns an int value of its amount attribute. Initiates create_database_sqlite() to check
    if database exists or to create it if doesn't.
    """
    sql_connection = sqlite3.connect("database.db")
    cursor = sql_connection.cursor()
    query = """
    SELECT amount FROM 'backpack' 
    WHERE name = ?
        hero_id = ?
    """
    name = item_name
    heros_id = hero_id
    cursor.execute(query, (name, heros_id))
    requested_row = cursor.fetchone()
    sql_connection.commit()
    sql_connection.close()
    amount, = requested_row
    return amount


def update_database(table_name, hero_id, item_name, item_type, modifier_amount):
    """
    Takes in table_name, item_name, item_type and modifier_amount. After checking which table to update,
    from database, modifies item_name's attributes (type and amount) with item_type and modifier_amount.
    Initiates create_database_sqlite() to check if database exists or to create it if not.
    """
    if table_name == "inventory":
        key = "modifier"
    else:
        key = "amount"
    sql_connection = sqlite3.connect("database.db")
    cursor = sql_connection.cursor()
    query = """
    UPDATE {}
    SET type = :type,
        {} = :modifier_amount
    WHERE name = :name AND hero_id = :hero_id;
    """.format(table_name, key)
    dictionary = {"name": item_name, "type": item_type, "modifier_amount": modifier_amount, "hero_id": hero_id}
    cursor.execute(query, dictionary)
    sql_connection.commit()
    sql_connection.close()


def remove_from_database(item_name, hero_id):
    """
    Takes in item_name and removes its entire row from database.db. Initiates create_database_sqlite() to check if
    database exists or to create it if not.
    """
    sql_connection = sqlite3.connect("database.db")
    cursor = sql_connection.cursor()
    query = """
    DELETE from 'backpack' WHERE name = ? AND hero_id = ?;
    """
    name = item_name
    heros_id = hero_id
    cursor.execute(query, (name, heros_id, ))
    sql_connection.commit()
    sql_connection.close()


class Inventory:
    """
    Creates object type Backpack that includes a list of equipment.
    """

    def __init__(self, capacity, hero_id):
        self.capacity = capacity
        self.max_capacity = capacity
        self.hero_id = hero_id
        create_database_sqlite(self.hero_id)

    def __str__(self):
        """
        Return string representation of the type Backpack instance.
        """
        length_of_backpack = len(return_rows_from_database('backpack', self.hero_id, True))
        difference = self.max_capacity - length_of_backpack
        return f"Hero's equipment:\n{return_rows_from_database('inventory', self.hero_id,  True)}.\n" \
               f"Hero's backpack has {length_of_backpack} items_backpack inside and has space for {difference} more\n" \
               f"Backpack: {return_rows_from_database('backpack', self.hero_id, True)}"

    def add_new_item(self, item_name, item_type, modifier_amount):
        """
        Takes in args and creates item in database. If item already exists in database, function is updating the
        item's amount.
        """
        if self.capacity:
            if item_name in [element["name"] for element in return_rows_from_database("inventory", self.hero_id)]:
                update_database("inventory", self.hero_id, item_name, item_type, modifier_amount)
            else:
                if item_name in [element["name"] for element in return_rows_from_database("backpack", self.hero_id)]:
                    item_amount = return_amount_from_database_item(item_name, self.hero_id)
                    new_value = item_amount + modifier_amount
                    update_database("backpack", self.hero_id, item_name, item_type, new_value)
                else:
                    insert_data_to_database(item_name, self.hero_id, item_type, modifier_amount)
                    self.capacity -= 1
        elif not self.capacity:
            print("No more room in your backpack")

    def remove_item(self, item):
        """
        Removes item's row from database.
        """
        for element in return_rows_from_database("backpack", self.hero_id):
            if element["name"] == item:
                if element["amount"] > 1:
                    update_database("backpack", self.hero_id, item, element["type"], element["amount"] - 1)
                    if element["amount"] == 0:
                        remove_from_database(item, self.hero_id)
                        self.capacity += 1
                else:
                    remove_from_database(item, self.hero_id)
                    self.capacity += 1


# if __name__ == "__main__":
#     inventory = Inventory()
    # print(inventory)
    # return_amount_from_database_item("HP potion")
    # inventory.add_new_item("Armor", "Plate Armor", "+60 armor")
    # inventory.add_new_item("Helmet", "Plate Helmet", "+60 armor")
    # inventory.add_new_item("Boots", "Plate Boots", "+60 armor")
    # inventory.add_new_item("HP potion", "small", 2)
    # inventory.add_new_item("Stamina potion", "small", 2)
    # inventory.add_new_item("Mana potion", "small", 2)
    # print(inventory)
    # inventory.add_new_item("Capacity potion", "small", 2)
    # inventory.remove_item("Stamina potion")
    # print(inventory)
