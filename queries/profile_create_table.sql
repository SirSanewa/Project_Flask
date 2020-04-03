CREATE TABLE IF NOT EXISTS "profile" (
            "id"            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            "name"          TEXT UNIQUE,
            "level"         INTEGER,
            "exp"           INTEGER,
            "hp"            INTEGER,
            "mana"          INTEGER,
            "stamina"       INTEGER,
            "armor"         INTEGER,
            "attack dmg"    INTEGER,
            "chance to crit" INTEGER,
            "chance to steal"INTEGER,
            "capacity"      INTEGER
            );