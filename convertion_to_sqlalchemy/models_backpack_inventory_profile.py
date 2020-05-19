from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, Boolean, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AllItemsInventory(Base):
    __tablename__ = "all_inventory_items"

    item_id = Column(Integer, primary_key=True)
    image = Column(LargeBinary, nullable=False)
    name = Column(String(255))

    attack_dmg = Column(Integer)
    chance_to_crit = Column(Float)
    max_hp = Column(Integer)
    max_mana = Column(Integer)
    max_stamina = Column(Integer)
    armor = Column(Integer)
    chance_to_steal = Column(Float)

    price = Column(Integer)
    type = Column(String(255))


class AllItemsBackpack(Base):
    __tablename__ = "all_backpack_items"

    item_id = Column(Integer, primary_key=True)
    image = Column(LargeBinary, nullable=False)
    name = Column(String(255))

    attack_dmg = Column(Integer)
    chance_to_crit = Column(Float)
    max_hp = Column(Integer)
    max_mana = Column(Integer)
    max_stamina = Column(Integer)
    armor = Column(Integer)
    chance_to_steal = Column(Float)
    hp = Column(Integer)
    mana = Column(Integer)

    price = Column(Integer)
    type = Column(String(255))


class BackpackItem(Base):
    __tablename__ = "backpack"

    item_id = Column(Integer, primary_key=True)
    hero_id = Column(Integer, unique=False)
    name = Column(String(255), ForeignKey("all_backpack_items.name"))
    amount = Column(Integer)

    item_data = relationship(AllItemsBackpack)


class InventoryItem(Base):
    __tablename__ = "inventory"

    item_id = Column(Integer, primary_key=True)
    hero_id = Column(Integer, unique=False)
    name = Column(String(255), ForeignKey("all_inventory_items.name"))

    item_data = relationship(AllItemsInventory)


class Quests(Base):
    __tablename__ = "quests"

    id = Column(Integer, autoincrement=True, primary_key=True)
    hero_id = Column(Integer, nullable=False)
    quest_1 = Column(Boolean, default=False)
    quest_2 = Column(Boolean, default=False)


class Profile(Base):
    __tablename__ = "profile"

    id = Column(Integer, ForeignKey("inventory.hero_id"), ForeignKey("backpack.hero_id"), ForeignKey("quests.hero_id"), primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    login = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    hp = Column(Integer, default=150)
    max_hp = Column(Integer, default=150)
    mana = Column(Integer, default=100)
    max_mana = Column(Integer, default=100)
    stamina = Column(Integer, default=100)
    max_stamina = Column(Integer, default=100)
    armor = Column(Integer, default=50)
    attack_dmg = Column(Integer, default=10)
    chance_to_steal = Column(Float, default=0.10)
    chance_to_crit = Column(Float, default=0.15)
    capacity = Column(Integer, default=10)
    money = Column(Integer, default=100)

    inventory = relationship(InventoryItem, viewonly=True, uselist=True)
    backpack = relationship(BackpackItem, viewonly=True, uselist=True)
    quests = relationship(Quests, viewonly=True)


class Monster(Base):
    __tablename__ = "monster"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image = Column(LargeBinary, nullable=False)
    name = Column(String(255), nullable=False, unique=True)
    level = Column(Integer, default=1)
    hp = Column(Integer, default=150)
    max_hp = Column(Integer, default=150)
    mana = Column(Integer, default=100)
    max_mana = Column(Integer, default=100)
    stamina = Column(Integer, default=100)
    max_stamina = Column(Integer, default=100)
    armor = Column(Integer, default=50)
    attack_dmg = Column(Integer, default=10)
    chance_to_crit = Column(Float, default=0.15)
    exp_reward = Column(Integer, default=0)
    money_reward = Column(Integer, default=0)


if __name__ == "__main__":
    engine = create_engine("sqlite:///database.db")
    Base.metadata.create_all(engine)
