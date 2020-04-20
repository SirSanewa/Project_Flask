from models_backpack_inventory_profile import BackpackItem, InventoryItem, Profile
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

engine = create_engine("sqlite:///database2.db")
DBSession = sessionmaker(bind=engine)
session = DBSession()

items = [
    BackpackItem(hero_id=1, name="HP potion", type="small", amount=2),
    BackpackItem(hero_id=1, name="Mana potion", type="large", amount=2),
    InventoryItem(hero_id=2, name="Gloves", type="Dragon skin gloves", modifier="+5 armor"),
    InventoryItem(hero_id=2, name="Armor", type="Sunfire Cape", modifier="+500 HP"),
]

session.bulk_save_objects(items)
session.commit()
