from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)
    date = Column(String)
    status = Column(String)
    description = Column(Text)
    local_path = Column(Text)
    url = Column(String, nullable=True)

# Placeholder models for skills, items, and related tables (to be expanded)
class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

class VideoSkill(Base):
    __tablename__ = 'video_skills'
    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True)
    __table_args__ = (
        PrimaryKeyConstraint('video_id', 'skill_id'),
    )

class VideoItem(Base):
    __tablename__ = 'video_items'
    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), primary_key=True)
    __table_args__ = (
        PrimaryKeyConstraint('video_id', 'item_id'),
    )

class VideoHero(Base):
    __tablename__ = 'video_heroes'
    video_id = Column(Integer, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True)
    hero_name = Column(String, primary_key=True)
    __table_args__ = (
        PrimaryKeyConstraint('video_id', 'hero_name'),
    )

# Placeholder for other tables referenced in indexes
class SkillRarity(Base):
    __tablename__ = 'skill_rarities'
    skill_id = Column(Integer, primary_key=True)
    rarity = Column(String)

class SkillType(Base):
    __tablename__ = 'skill_types'
    skill_id = Column(Integer, primary_key=True)
    type = Column(String)

class SkillHero(Base):
    __tablename__ = 'skill_heroes'
    skill_id = Column(Integer, primary_key=True)
    hero = Column(String)

class SkillEffect(Base):
    __tablename__ = 'skill_effects'
    skill_id = Column(Integer, primary_key=True)
    effect = Column(String)

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    size = Column(String)

class ItemRarity(Base):
    __tablename__ = 'item_rarities'
    item_id = Column(Integer, primary_key=True)
    rarity = Column(String)

class ItemType(Base):
    __tablename__ = 'item_types'
    item_id = Column(Integer, primary_key=True)
    type = Column(String)

class ItemHero(Base):
    __tablename__ = 'item_heroes'
    item_id = Column(Integer, primary_key=True)
    hero = Column(String)

class ItemEffect(Base):
    __tablename__ = 'item_effects'
    item_id = Column(Integer, primary_key=True)
    effect = Column(String)

class Enchantment(Base):
    __tablename__ = 'enchantments'
    item_id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    enchantment_name = Column(String, primary_key=True)
    enchantment_effect = Column(String, nullable=False)

# Define indexes
Index('idx_skill_name', Skill.name)
Index('idx_skill_rarity', SkillRarity.rarity)
Index('idx_skill_type', SkillType.type)
Index('idx_skill_hero', SkillHero.hero)
Index('idx_item_name', Item.name)
Index('idx_item_size', Item.size)
Index('idx_item_rarity', ItemRarity.rarity)
Index('idx_item_type', ItemType.type)
Index('idx_item_hero', ItemHero.hero)
Index('idx_enchantment_item_id', Enchantment.item_id)
Index('idx_video_date', Video.date)
Index('idx_video_skills', VideoSkill.video_id, VideoSkill.skill_id)
Index('idx_video_items', VideoItem.video_id, VideoItem.item_id)
Index('idx_video_heroes', VideoHero.video_id, VideoHero.hero_name)