from models_backpack_inventory_profile import BackpackItem, InventoryItem, AllItemsInventory, AllItemsBackpack, Profile
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import os

engine = create_engine("sqlite:///database2.db")
DBSession = sessionmaker(bind=engine)
session = DBSession()


items = [
    BackpackItem(hero_id=1, name="Hp_potion", amount=2),
    BackpackItem(hero_id=1, name="Brass_Armor"),
    Profile(name="test", login="test", password="test")
]

directory = "static/items"
for file in os.listdir(directory):
    with open(f"static/items/{file}", "rb") as f:
        byte_file = bytearray(f.read())
        file_name = file.split(".")
        items.append(AllItemsBackpack(image=byte_file, name=file_name[0]))

session.bulk_save_objects(items)
session.commit()

  # TODO: podzielić przzedmioty na backpack i inventory, stworzyć system wyświetlanie, przezroczstość po najechaniu, statystyki rpzedmiotów po najechaniu
