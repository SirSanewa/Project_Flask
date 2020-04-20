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

    id = Column(Integer, ForeignKey("inventory.hero_id"), ForeignKey("backpack.hero_id"), primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    login = Column(String(255), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    level = Column(Integer, default=0)
    exp = Column(Integer, default=0)
    hp = Column(Integer, default=150)
    mana = Column(Integer, default=100)
    stamina = Column(Integer, default=100)
    armor = Column(Integer, default=50)
    attack_dmg = Column(Integer, default=10)
    chance_to_steal = Column(Float, default=0.10)
    chance_to_crit = Column(Float, default=0.25)
    capacity = Column(Integer, default=10)

    inventory = relationship(InventoryItem, viewonly=True, uselist=True)
    backpack = relationship(BackpackItem, viewonly=True, uselist=True)


if __name__ == "__main__":
    engine = create_engine("sqlite:///convertion_to_sqlalchemy/database2.db")
    Base.metadata.create_all(engine)
