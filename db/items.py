from bs4 import BeautifulSoup
from db.db_routine import DBRoutine
from utils.config import RARITY_ORDER, SIZE_ORDER

class ItemDB:
    def __init__(self, db_routine: DBRoutine):
        self.db = db_routine

    def get_rarities(self):
        results = self.db.execute("SELECT DISTINCT rarity FROM item_rarities WHERE rarity IS NOT NULL")
        rarities = [row[0] for row in results]
        sorted_rarities = sorted([r for r in rarities if r in RARITY_ORDER], key=lambda x: RARITY_ORDER.index(x))
        return [""] + sorted_rarities

    def get_types(self):
        results = self.db.execute("SELECT DISTINCT type FROM item_types WHERE type IS NOT NULL ORDER BY type")
        return [row[0] for row in results]

    def get_heroes(self):
        results = self.db.execute("SELECT DISTINCT hero FROM item_heroes WHERE hero IS NOT NULL ORDER BY hero")
        return [""] + [row[0] for row in results]

    def get_sizes(self):
        results = self.db.execute("SELECT DISTINCT size FROM items WHERE size IS NOT NULL ORDER BY size")
        sizes = [row[0] for row in results]
        sorted_sizes = sorted([s for s in sizes if s in SIZE_ORDER], key=lambda x: SIZE_ORDER.index(x))
        return [""] + sorted_sizes

    def get_all_items(self):
        results = self.db.execute("SELECT id, name FROM items ORDER BY name")
        return [(row[0], row[1]) for row in results]

    def query_items(self, name="", rarities=None, types=None, effect_keyword="", heroes=None, size="", sort_by="name", sort_order="ASC"):
        query = """
            SELECT DISTINCT i.id, i.name, i.size,
                   GROUP_CONCAT(DISTINCT ir.rarity) as rarities,
                   GROUP_CONCAT(DISTINCT ie.effect) as effects,
                   GROUP_CONCAT(DISTINCT it.type) as types,
                   GROUP_CONCAT(DISTINCT ih.hero) as heroes,
                   GROUP_CONCAT(DISTINCT e.enchantment_name || ': ' || e.enchantment_effect) as enchantments
            FROM items i
            LEFT JOIN item_rarities ir ON i.id = ir.item_id
            LEFT JOIN item_effects ie ON i.id = ie.item_id
            LEFT JOIN item_types it ON i.id = it.item_id
            LEFT JOIN item_heroes ih ON i.id = ih.item_id
            LEFT JOIN enchantments e ON i.id = e.item_id
            WHERE 1=1
        """
        params = []
        if name:
            query += " AND i.name LIKE ?"
            params.append(f"%{name}%")
        if rarities:
            query += " AND i.id IN (SELECT item_id FROM item_rarities WHERE rarity IN ({}))".format(",".join("?" * len(rarities)))
            params.extend(rarities)
        if types:
            query += " AND i.id IN (SELECT item_id FROM item_types WHERE type IN ({}))".format(",".join("?" * len(types)))
            params.extend(types)
        if effect_keyword:
            query += " AND ie.effect LIKE ?"
            params.append(f"%{effect_keyword}%")
        if heroes:
            query += " AND (i.id IN (SELECT item_id FROM item_heroes WHERE hero IN ({})) OR i.id NOT IN (SELECT item_id FROM item_heroes))".format(",".join("?" * len(heroes)))
            params.extend(heroes)
        if size:
            query += " AND i.size = ?"
            params.append(size)
        query += " GROUP BY i.id"
        if sort_by == "name":
            query += f" ORDER BY i.name {sort_order}"
        elif sort_by == "rarity":
            query += f"""
                ORDER BY (
                    MIN(
                        CASE ir.rarity
                            WHEN 'Bronze' THEN 1
                            WHEN 'Silver' THEN 2
                            WHEN 'Gold' THEN 3
                            WHEN 'Diamond' THEN 4
                            WHEN 'Legendary' THEN 5
                            ELSE 6
                        END
                    )
                ) {sort_order}
            """
        elif sort_by == "types":
            query += f" ORDER BY GROUP_CONCAT(DISTINCT it.type) {sort_order}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
        
        items = []
        for row in results:
            effects = row["effects"] or ""
            if effects:
                soup = BeautifulSoup(effects, "html.parser")
                effects = soup.get_text(strip=True)
            effects_list = list(set(effects.split(","))) if effects else []
            types_list = list(set(row["types"].split(","))) if row["types"] else []
            rarities_list = sorted(
                [r for r in row["rarities"].split(",") if r] if row["rarities"] else [],
                key=lambda x: RARITY_ORDER.index(x) if x in RARITY_ORDER else len(RARITY_ORDER)
            )
            heroes_list = list(set(row["heroes"].split(","))) if row["heroes"] else []
            enchantments_list = list(set(row["enchantments"].split(","))) if row["enchantments"] else []
            items.append({
                "id": row["id"],
                "name": row["name"],
                "size": row["size"],
                "rarities": ", ".join(rarities_list),
                "effects": ", ".join(effects_list),
                "types": types_list,
                "heroes": heroes_list,
                "enchantments": ", ".join(enchantments_list)
            })
        return items