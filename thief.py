from main import Hero


class Thief(Hero):
    def __init__(self,
                 name=None,
                 login=None,
                 password=None,
                 hp=100,
                 mana=50,
                 stamina=100,
                 armor=20,
                 attack_dmg=10,
                 chance_to_steal=30,
                 chance_to_crit=40,
                 capacity=10, ):
        if name is None:
            hero_name = self.__class__.__name__
        else:
            hero_name = name
        super().__init__(hero_name,
                         login,
                         password,
                         hp,
                         mana,
                         stamina,
                         armor,
                         attack_dmg,
                         chance_to_steal,
                         chance_to_crit,
                         capacity)


if __name__ == "__main__":
    thief = Thief("Wukasz", 1, 1, 1, 1, 1, 1, 1, 10)
    # print(thief)
    # thief.add_item("Armor", "Plate Armor", "+50 armor, +1 hp, -45 mana")
    thief.add_item("Weapon", "Plate Armor", "+20 attack_dmg, -99 stamina, +20 chance_to_crit")
    print(thief.backpack)
    thief.add_item("Mana potion", "small", 2)
    print(thief.backpack)
    thief.backpack.remove_item("Mana potion")
    print(thief.backpack)
