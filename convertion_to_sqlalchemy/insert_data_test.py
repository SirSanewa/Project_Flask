from models_backpack_inventory_profile import BackpackItem, InventoryItem, Profile
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

engine = create_engine("sqlite:///database2.db")
DBSession = sessionmaker(bind=engine)
session = DBSession()

items = [
    Profile(id=1, name="Luke", login="test", password="test", level=1, exp=0, hp=100, mana=100, stamina=100, armor=50,
            attack_dmg=10, chance_to_steal=0.1, chance_to_crit=0.2, capacity=10),
    BackpackItem(hero_id=1, name="HP potion", type="small", amount=2),
    BackpackItem(hero_id=1, name="Mana potion", type="large", amount=2),
    InventoryItem(hero_id=1, name="Gloves", type="Dragon skin gloves", modifier="+5 armor"),
    InventoryItem(hero_id=1, name="Armor", type="Sunfire Cape", modifier="+500 HP"),
]

session.bulk_save_objects(items)
session.commit()
