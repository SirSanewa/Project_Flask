import unittest
from flask_main import create_modifier


class AllTest(unittest.TestCase):
    def test_create_modifier_1(self):
        dictionary = {"attack_dmg": "50"}
        result = create_modifier(dictionary)
        expected_result = "+50 attack_dmg "

        self.assertEqual(expected_result, result)

    def test_create_modifier_2(self):
        dictionary = {"attack_dmg": 50, "chance_to_crit": 20, "max_hp": 100}
        result = create_modifier(dictionary)
        expected_result = "+50 attack_dmg +20 chance_to_crit +100 max_hp "

        self.assertEqual(expected_result, result)


if __name__ == "__main__":
    unittest.main()