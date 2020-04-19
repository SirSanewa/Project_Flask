from models_backpack_inventory_profile import BackpackItem, InventoryItem, Profile
from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker

engine = create_engine("sqlite:///database2.db")
DBSession = sessionmaker(bind=engine)
session = DBSession()

result = session.query(Profile).filter(Profile.id == 1).all()

for element in result:
    print(f"{element.name}(ID: {element.id}) ma na sobie:")
    for item in element.inventory:
        print("-", item.name, item.type, item.modifier)
    print("A w plecaku:")
    for item in element.backpack:
        print("-", item.name, item.type, item.amount)
