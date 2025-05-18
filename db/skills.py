from bs4 import BeautifulSoup
from db.db_routine import DBRoutine
from utils.config import RARITY_ORDER

class SkillDB:
    def __init__(self, db_routine: DBRoutine):
        self.db = db_routine

    def get_rarities(self):
        results = self.db.execute("SELECT DISTINCT rarity FROM skill_rarities WHERE rarity IS NOT NULL")
        rarities = [row[0] for row in results]
        sorted_rarities = sorted([r for r in rarities if r in RARITY_ORDER], key=lambda x: RARITY_ORDER.index(x))
        return [""] + sorted_rarities

    def get_heroes(self):
        results = self.db.execute("""
            SELECT DISTINCT hero FROM (
                SELECT hero FROM skill_heroes WHERE hero IS NOT NULL
                UNION
                SELECT hero FROM item_heroes WHERE hero IS NOT NULL
            ) ORDER BY hero
        """)
        return [""] + [row[0] for row in results]

    def get_types(self):
        results = self.db.execute("SELECT DISTINCT type FROM skill_types WHERE type IS NOT NULL ORDER BY type")
        return [row[0] for row in results]

    def get_all_skills(self):
        results = self.db.execute("SELECT id, name FROM skills ORDER BY name")
        return [(row[0], row[1]) for row in results]

    def query_skills(self, name="", rarities=None, types=None, effect_keyword="", heroes=None, sort_by="name", sort_order="ASC"):
        query = """
            SELECT DISTINCT s.id, s.name,
                   GROUP_CONCAT(DISTINCT sr.rarity) as rarities,
                   GROUP_CONCAT(DISTINCT se.effect) as effects,
                   GROUP_CONCAT(DISTINCT st.type) as types,
                   GROUP_CONCAT(DISTINCT sh.hero) as heroes
            FROM skills s
            LEFT JOIN skill_rarities sr ON s.id = sr.skill_id
            LEFT JOIN skill_effects se ON s.id = se.skill_id
            LEFT JOIN skill_types st ON s.id = st.skill_id
            LEFT JOIN skill_heroes sh ON s.id = sh.skill_id
            WHERE 1=1
        """
        params = []
        if name:
            query += " AND s.name LIKE ?"
            params.append(f"%{name}%")
        if rarities:
            query += " AND s.id IN (SELECT skill_id FROM skill_rarities WHERE rarity IN ({}))".format(",".join("?" * len(rarities)))
            params.extend(rarities)
        if types:
            query += " AND s.id IN (SELECT skill_id FROM skill_types WHERE type IN ({}))".format(",".join("?" * len(types)))
            params.extend(types)
        if effect_keyword:
            query += " AND se.effect LIKE ?"
            params.append(f"%{effect_keyword}%")
        if heroes:
            query += " AND s.id IN (SELECT skill_id FROM skill_heroes WHERE hero IN ({}))".format(",".join("?" * len(heroes)))
            params.extend(heroes)
        query += " GROUP BY s.id"
        if sort_by == "name":
            query += f" ORDER BY s.name {sort_order}"
        elif sort_by == "rarity":
            query += f"""
                ORDER BY (
                    MIN(
                        CASE sr.rarity
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
            query += f" ORDER BY GROUP_CONCAT(DISTINCT st.type) {sort_order}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
        
        skills = []
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
            skills.append({
                "id": row["id"],
                "name": row["name"],
                "rarities": ", ".join(rarities_list),
                "effects": ", ".join(effects_list),
                "types": types_list,
                "heroes": heroes_list
            })
        return skills