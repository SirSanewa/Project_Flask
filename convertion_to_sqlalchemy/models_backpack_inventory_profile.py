from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class BackpackItem(Base):
    __tablename__ = "backpack"

    item_id = Column(Integer, primary_key=True)
    hero_id = Column(Integer, unique=False)
    name = Column(String(255))
    type = Column(String(255))
    amount = Column(Integer)


class InventoryItem(Base):
    __tablename__ = "inventory"

    item_id = Column(Integer, primary_key=True)
    hero_id = Column(Integer, unique=False)
    name = Column(String(255))
    type = Column(String(255))
    modifier = Column(String(255))


class Profile(Base):
    __tablename__ = "profile"

    id = Column(Integer, ForeignKey("inventory.hero_id"), ForeignKey("backpack.hero_id"), primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    login = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    level = Column(Integer)
    exp = Column(Integer)
    hp = Column(Integer)
    mana = Column(Integer)
    stamina = Column(Integer)
    armor = Column(Integer)
    attack_dmg = Column(Integer)
    chance_to_steal = Column(Float)
    chance_to_crit = Column(Float)
    capacity = Column(Integer)

    inventory = relationship(InventoryItem, viewonly=True, uselist=True)
    backpack = relationship(BackpackItem, viewonly=True, uselist=True)


if __name__ == "__main__":
    engine = create_engine("sqlite:///convertion_to_sqlalchemy/database2.db")
    Base.metadata.create_all(engine)
