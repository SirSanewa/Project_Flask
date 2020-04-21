from models_backpack_inventory_profile import BackpackItem, InventoryItem, AllItemsInventory, AllItemsBackpack, Profile
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

engine = create_engine("sqlite:///database2.db")
DBSession = sessionmaker(bind=engine)
session = DBSession()

items = [
    BackpackItem(hero_id=1, name="HP potion small", amount=2),
    InventoryItem(hero_id=1, name="Brass Armor"),
    AllItemsInventory(image="test obrazka", name="Brass Armor", modifier="+5 armor"),
    AllItemsBackpack(image="test obrazka", name="HP potion small"),
    Profile(name="test", login="test", password="test")
]

session.bulk_save_objects(items)
session.commit()
