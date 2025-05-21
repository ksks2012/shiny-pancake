from db.db_routine import DBRoutine
from db.models import Video, VideoSkill, VideoItem, VideoHero, Skill, Item, SkillHero, ItemHero
from sqlalchemy import select, func, union, and_
from sqlalchemy.sql import text

class VideoDB:
    def __init__(self, db_routine: DBRoutine):
        self.db = db_routine

    def get_all_heroes(self):
        with self.db.get_connection() as session:
            # Union skill_heroes and item_heroes, select distinct heroes
            skill_heroes = select(SkillHero.hero).where(SkillHero.hero != None)
            item_heroes = select(ItemHero.hero).where(ItemHero.hero != None)
            query = union(skill_heroes, item_heroes).order_by('hero')
            result = session.execute(query)
            return [row[0] for row in result.fetchall()]

    def get_videos(self, video_type="", status="", skill_ids=None, item_ids=None, hero_name="", sort_by="date", sort_order="DESC"):
        with self.db.get_connection() as session:
            query = (
                session.query(
                    Video.id,
                    Video.title,
                    Video.type,
                    Video.date,
                    Video.status,
                    Video.description,
                    Video.local_path,
                    Video.url,
                    func.group_concat(Skill.name.distinct()).label('skills'),
                    func.group_concat(Item.name.distinct()).label('items'),
                    func.group_concat(VideoHero.hero_name.distinct()).label('heroes')
                )
                .outerjoin(VideoSkill, Video.id == VideoSkill.video_id)
                .outerjoin(Skill, VideoSkill.skill_id == Skill.id)
                .outerjoin(VideoItem, Video.id == VideoItem.video_id)
                .outerjoin(Item, VideoItem.item_id == Item.id)
                .outerjoin(VideoHero, Video.id == VideoHero.video_id)
            )

            filters = []
            if video_type:
                filters.append(Video.type == video_type)
            if status:
                filters.append(Video.status == status)
            if skill_ids:
                query = query.filter(Video.id.in_(
                    select(VideoSkill.video_id).where(VideoSkill.skill_id.in_(skill_ids))
                ))
            if item_ids:
                query = query.filter(Video.id.in_(
                    select(VideoItem.video_id).where(VideoItem.item_id.in_(item_ids))
                ))
            if hero_name and hero_name != "":
                query = query.filter(Video.id.in_(
                    select(VideoHero.video_id).where(VideoHero.hero_name == hero_name)
                ))

            query = (
                query
                .filter(and_(*filters))
                .group_by(Video.id)
                .order_by(text(f"videos.{sort_by} {sort_order}"))
            )

            results = query.all()
            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "type": row.type,
                    "date": row.date,
                    "status": row.status,
                    "description": row.description,
                    "local_path": row.local_path or "",
                    "url": row.url or "",
                    "skills": row.skills or "",
                    "items": row.items or "",
                    "heroes": row.heroes or ""
                }
                for row in results
            ]

    def add_video(self, title, video_type, date, status, description, skill_ids, item_ids, hero_names, local_path="", url=""):
        with self.db.get_connection() as session:
            video = Video(
                title=title,
                type=video_type,
                date=date,
                status=status,
                description=description,
                local_path=local_path or None,
                url=url or None
            )
            session.add(video)
            session.flush()

            for skill_id in skill_ids:
                session.add(VideoSkill(video_id=video.id, skill_id=skill_id))
            for item_id in item_ids:
                session.add(VideoItem(video_id=video.id, item_id=item_id))
            for hero_name in hero_names:
                session.add(VideoHero(video_id=video.id, hero_name=hero_name))

    def update_video(self, video_id, title, video_type, date, status, description, skill_ids, item_ids, hero_names, local_path="", url=""):
        with self.db.get_connection() as session:
            video = session.get(Video, video_id)
            if not video:
                raise ValueError(f"Video with id {video_id} not found")

            video.title = title
            video.type = video_type
            video.date = date
            video.status = status
            video.description = description
            video.local_path = local_path or None
            video.url = url or None

            session.query(VideoSkill).filter(VideoSkill.video_id == video_id).delete()
            session.query(VideoItem).filter(VideoItem.video_id == video_id).delete()
            session.query(VideoHero).filter(VideoHero.video_id == video_id).delete()

            # Add new junction table entries
            for skill_id in skill_ids:
                session.add(VideoSkill(video_id=video_id, skill_id=skill_id))
            for item_id in item_ids:
                session.add(VideoItem(video_id=video_id, item_id=item_id))
            for hero_name in hero_names:
                session.add(VideoHero(video_id=video_id, hero_name=hero_name))

    def delete_video(self, video_id):
        with self.db.get_connection() as session:
            video = session.get(Video, video_id)
            if video:
                session.delete(video)

    def get_video_associations(self, title):
        """Fetch skill_ids, item_ids, and hero_names associated with a video by title."""
        with self.db.get_connection() as session:
            video = session.query(Video).filter(Video.title == title).first()
            if not video:
                return [], [], []

            skill_ids = [
                vs.skill_id for vs in session.query(VideoSkill.skill_id)
                .filter(VideoSkill.video_id == video.id)
                .all()
            ]
            item_ids = [
                vi.item_id for vi in session.query(VideoItem.item_id)
                .filter(VideoItem.video_id == video.id)
                .all()
            ]
            hero_names = [
                vh.hero_name for vh in session.query(VideoHero.hero_name)
                .filter(VideoHero.video_id == video.id)
                .all()
            ]

            return skill_ids, item_ids, hero_names