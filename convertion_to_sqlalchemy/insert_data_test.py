from models_backpack_inventory_profile import BackpackItem, InventoryItem, AllItemsInventory, AllItemsBackpack, Profile
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import os

engine = create_engine("sqlite:///database2.db")
DBSession = sessionmaker(bind=engine)
session = DBSession()

items = [
    BackpackItem(hero_id=1, name="Hp_Potion", amount=2),
    InventoryItem(hero_id=1, name="Brass_Armor"),
    InventoryItem(hero_id=1, name="Blacksteel_Sword"),
    InventoryItem(hero_id=1, name="Crocodile_Boots"),
    InventoryItem(hero_id=1, name="Demon_Helmet"),
    InventoryItem(hero_id=1, name="Ancient_Shield"),
    InventoryItem(hero_id=2, name="Ancient_Shield"),
    InventoryItem(hero_id=1, name="Brass_Legs"),
    Profile(name="test", login="test", password="test"),
    Profile(name="test2", login="test2", password="test")
]

directory = "static/items_backpack"
for file in os.listdir(directory):
    with open(f"{directory}/{file}", "rb") as f:
        byte_file = bytearray(f.read())
        file_name = file.split(".")
        items.append(AllItemsBackpack(image=byte_file, name=file_name[0]))

directory = "static/items_inventory"
for file in os.listdir(directory):
    with open(f"{directory}/{file}", "rb") as f:
        byte_file = bytearray(f.read())
        file_name = file.split(".")
        items.append(AllItemsInventory(image=byte_file, name=file_name[0]))
session.bulk_save_objects(items)
session.commit()

# TODO: przezroczstość po najechaniu, statystyki rpzedmiotów po najechaniu
