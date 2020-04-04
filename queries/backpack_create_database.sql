CREATE TABLE IF NOT EXISTS "inventory" (
        "hero_id"   INTEGER PRIMARY KEY,
        "name"      TEXT UNIQUE,
        "type"      TEXT,
        "modifier"  TEXT,
        FOREIGN KEY ("hero_id") REFERENCES "profile" ("id")
    );
    INSERT OR IGNORE INTO "inventory" ("name", "type", "modifier")
    VALUES  ("Helmet", NULL, NULL),
            ("Armor", NULL, NULL),
            ("Gloves", NULL, NULL),
            ("Boots", NULL, NULL),
            ("Weapon", NULL, NULL);
    CREATE TABLE IF NOT EXISTS "backpack" (
        "hero_id"   INTEGER,
        "name"      TEXT,
        "type"      TEXT,
        "amount"    INTEGER,
        FOREIGN KEY ("hero_id") REFERENCES "profile" ("id")
    );