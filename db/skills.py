from db.db_routine import DBRoutine
from db.models import Skill, SkillRarity, SkillType, SkillEffect, SkillHero, ItemHero
from utils.config import RARITY_ORDER
from sqlalchemy import select, func, union, and_, case
from sqlalchemy.sql import text

class SkillDB:
    def __init__(self, db_routine: DBRoutine):
        self.db = db_routine

    def get_rarities(self):
        with self.db.get_connection() as session:
            results = session.query(SkillRarity.rarity).distinct().all()
            rarities = [row[0] for row in results if row[0] is not None]
            sorted_rarities = sorted([r for r in rarities if r in RARITY_ORDER], key=lambda x: RARITY_ORDER.index(x))
            return [""] + sorted_rarities

    def get_heroes(self):
        with self.db.get_connection() as session:
            skill_heroes = select(SkillHero.hero).where(SkillHero.hero != None)
            item_heroes = select(ItemHero.hero).where(ItemHero.hero != None)
            query = union(skill_heroes, item_heroes).order_by('hero')
            result = session.execute(query)
            return [""] + [row[0] for row in result.fetchall()]

    def get_types(self):
        with self.db.get_connection() as session:
            results = session.query(SkillType.type).distinct().order_by(SkillType.type).all()
            return [row[0] for row in results]

    def get_all_skills(self):
        with self.db.get_connection() as session:
            results = session.query(Skill.id, Skill.name).order_by(Skill.name).all()
            return [(row.id, row.name) for row in results]

    def query_skills(self, name="", rarities=None, types=None, effect_keyword="", heroes=None, sort_by="name", sort_order="ASC"):
        with self.db.get_connection() as session:
            # Base query with joins
            query = (
                session.query(
                    Skill.id,
                    Skill.name,
                    func.group_concat(SkillRarity.rarity.distinct()).label('rarities'),
                    func.group_concat(SkillEffect.effect.distinct()).label('effects'),
                    func.group_concat(SkillType.type.distinct()).label('types'),
                    func.group_concat(SkillHero.hero.distinct()).label('heroes')
                )
                .outerjoin(SkillRarity, Skill.id == SkillRarity.skill_id)
                .outerjoin(SkillEffect, Skill.id == SkillEffect.skill_id)
                .outerjoin(SkillType, Skill.id == SkillType.skill_id)
                .outerjoin(SkillHero, Skill.id == SkillHero.skill_id)
            )

            # Apply filters
            filters = []
            if name:
                filters.append(Skill.name.ilike(f"%{name}%"))
            if rarities:
                query = query.filter(Skill.id.in_(
                    select(SkillRarity.skill_id).where(SkillRarity.rarity.in_(rarities))
                ))
            if types:
                query = query.filter(Skill.id.in_(
                    select(SkillType.skill_id).where(SkillType.type.in_(types))
                ))
            if effect_keyword:
                filters.append(SkillEffect.effect.ilike(f"%{effect_keyword}%"))
            if heroes:
                query = query.filter(Skill.id.in_(
                    select(SkillHero.skill_id).where(SkillHero.hero.in_(heroes))
                ))

            # Apply filters and group
            query = query.filter(and_(*filters)).group_by(Skill.id)

            # Apply sorting
            if sort_by == "name":
                query = query.order_by(text(f"skills.name {sort_order}"))
            elif sort_by == "rarity":
                rarity_case = case(
                    {rarity: idx + 1 for idx, rarity in enumerate(['Bronze', 'Silver', 'Gold', 'Diamond', 'Legendary'])},
                    value=SkillRarity.rarity,
                    else_=6
                )
                query = query.order_by(func.min(rarity_case).asc() if sort_order == "ASC" else func.min(rarity_case).desc())
            elif sort_by == "types":
                query = query.order_by(text(f"GROUP_CONCAT(DISTINCT skill_types.type) {sort_order}"))

            # Execute and format results
            results = query.all()
            skills = []
            for row in results:
                # Process effects (assuming plain text, no HTML)
                effects = row.effects or ""
                effects_list = sorted(list(set(effects.split(","))) if effects else [], key=str.lower)
                
                # Process types
                types_list = sorted(list(set(row.types.split(","))) if row.types else [], key=str.lower)
                
                # Process rarities
                rarities_list = sorted(
                    [r for r in (row.rarities.split(",") if row.rarities else []) if r],
                    key=lambda x: RARITY_ORDER.index(x) if x in RARITY_ORDER else len(RARITY_ORDER)
                )
                
                # Process heroes
                heroes_list = sorted(list(set(row.heroes.split(","))) if row.heroes else [], key=str.lower)
                
                skills.append({
                    "id": row.id,
                    "name": row.name,
                    "rarities": ", ".join(rarities_list),
                    "effects": ", ".join(effects_list),
                    "types": types_list,
                    "heroes": heroes_list
                })
            
            return skills