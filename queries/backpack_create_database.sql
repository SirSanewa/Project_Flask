CREATE TABLE IF NOT EXISTS "inventory" (
        "hero_id"   INTEGER,
        "name"      TEXT,
        "type"      TEXT,
        "modifier"  TEXT,
        FOREIGN KEY ("hero_id") REFERENCES "profile" ("id")
    );
CREATE TABLE IF NOT EXISTS "backpack" (
    "hero_id"   INTEGER,
    "name"      TEXT,
    "type"      TEXT,
    "amount"    INTEGER,
    FOREIGN KEY ("hero_id") REFERENCES "profile" ("id")
);