from models_backpack_inventory_profile import BackpackItem, InventoryItem, AllItemsInventory, AllItemsBackpack, Profile
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker
import os

engine = create_engine("sqlite:///database2.db")
DBSession = sessionmaker(bind=engine)
session = DBSession()

items = [
    Profile(name="test", login="test", password="test"),
]

directory = "static/items_inventory"
for file in os.listdir(directory):
    with open(f"{directory}/{file}", "rb") as f:
        byte_file = bytearray(f.read())
        file_name = file.split("|")
        item_elements = file_name[0].split(",")
        item_name = item_elements[0]
        modifier = item_elements[1]
        price = item_elements[2].split(".")[0]
        item_type = item_name.split("_")[1]
        if item_type in ["Axe", "Mace", "Sword", "Dagger"]:
            item_type = "Weapon"
        items.append(AllItemsInventory(image=byte_file, name=item_name, modifier=modifier, price=price, type=item_type))

# directory = "static/items_backpack"
# for file in os.listdir(directory):
#     with open(f"{directory}/{file}", "rb") as f:
#         byte_file = bytearray(f.read())
#         file_name = file.split(".")
#         items.append(AllItemsBackpack(image=byte_file, name=file_name[0]))
session.bulk_save_objects(items)
session.commit()
