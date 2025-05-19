from db.db_routine import DBRoutine
from db.models import Item, ItemRarity, ItemType, ItemEffect, ItemHero, Enchantment
from utils.config import RARITY_ORDER, SIZE_ORDER
from sqlalchemy import select, func, and_, case
from sqlalchemy.sql import text

class ItemDB:
    def __init__(self, db_routine: DBRoutine):
        self.db = db_routine

    def get_rarities(self):
        with self.db.get_connection() as session:
            results = session.query(ItemRarity.rarity).distinct().all()
            rarities = [row[0] for row in results if row[0] is not None]
            sorted_rarities = sorted([r for r in rarities if r in RARITY_ORDER], key=lambda x: RARITY_ORDER.index(x))
            return [""] + sorted_rarities

    def get_types(self):
        with self.db.get_connection() as session:
            results = session.query(ItemType.type).distinct().order_by(ItemType.type).all()
            return [row[0] for row in results]

    def get_heroes(self):
        with self.db.get_connection() as session:
            results = session.query(ItemHero.hero).distinct().order_by(ItemHero.hero).all()
            return [""] + [row[0] for row in results if row[0] is not None]

    def get_sizes(self):
        with self.db.get_connection() as session:
            results = session.query(Item.size).distinct().all()
            sizes = [row[0] for row in results if row[0] is not None]
            sorted_sizes = sorted([s for s in sizes if s in SIZE_ORDER], key=lambda x: SIZE_ORDER.index(x))
            return [""] + sorted_sizes

    def get_all_items(self):
        with self.db.get_connection() as session:
            results = session.query(Item.id, Item.name).order_by(Item.name).all()
            return [(row.id, row.name) for row in results]

    def query_items(self, name="", rarities=None, types=None, effect_keyword="", heroes=None, size="", sort_by="name", sort_order="ASC"):
        with self.db.get_connection() as session:
            # Base query with joins
            query = (
                session.query(
                    Item.id,
                    Item.name,
                    Item.size,
                    func.group_concat(ItemRarity.rarity.distinct()).label('rarities'),
                    func.group_concat(ItemEffect.effect.distinct()).label('effects'),
                    func.group_concat(ItemType.type.distinct()).label('types'),
                    func.group_concat(ItemHero.hero.distinct()).label('heroes'),
                    func.group_concat(
                        func.concat(Enchantment.enchantment_name, ': ', Enchantment.enchantment_effect).distinct()
                    ).label('enchantments')
                )
                .outerjoin(ItemRarity, Item.id == ItemRarity.item_id)
                .outerjoin(ItemEffect, Item.id == ItemEffect.item_id)
                .outerjoin(ItemType, Item.id == ItemType.item_id)
                .outerjoin(ItemHero, Item.id == ItemHero.item_id)
                .outerjoin(Enchantment, Item.id == Enchantment.item_id)
            )

            # Apply filters
            filters = []
            if name:
                filters.append(Item.name.ilike(f"%{name}%"))
            if rarities:
                query = query.filter(Item.id.in_(
                    select(ItemRarity.item_id).where(ItemRarity.rarity.in_(rarities))
                ))
            if types:
                query = query.filter(Item.id.in_(
                    select(ItemType.item_id).where(ItemType.type.in_(types))
                ))
            if effect_keyword:
                filters.append(ItemEffect.effect.ilike(f"%{effect_keyword}%"))
            if heroes:
                query = query.filter(
                    and_(
                        Item.id.in_(
                            select(ItemHero.item_id).where(ItemHero.hero.in_(heroes))
                        ) |
                        (~Item.id.in_(
                            select(ItemHero.item_id)
                        ))
                    )
                )
            if size:
                filters.append(Item.size == size)

            # Apply filters and group
            query = query.filter(and_(*filters)).group_by(Item.id)

            # Apply sorting
            if sort_by == "name":
                query = query.order_by(text(f"items.name {sort_order}"))
            elif sort_by == "rarity":
                rarity_case = case(
                    {rarity: idx + 1 for idx, rarity in enumerate(['Bronze', 'Silver', 'Gold', 'Diamond', 'Legendary'])},
                    value=ItemRarity.rarity,
                    else_=6
                )
                query = query.order_by(func.min(rarity_case).asc() if sort_order == "ASC" else func.min(rarity_case).desc())
            elif sort_by == "types":
                query = query.order_by(text(f"GROUP_CONCAT(DISTINCT item_types.type) {sort_order}"))

            # Execute and format results
            results = query.all()
            items = []
            for row in results:
                # Process effects (assuming plain text)
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
                
                # Process enchantments
                enchantments_list = sorted(list(set(row.enchantments.split(","))) if row.enchantments else [], key=str.lower)
                
                items.append({
                    "id": row.id,
                    "name": row.name,
                    "size": row.size,
                    "rarities": ", ".join(rarities_list),
                    "effects": ", ".join(effects_list),
                    "types": types_list,
                    "heroes": heroes_list,
                    "enchantments": ", ".join(enchantments_list)
                })
            
            return items