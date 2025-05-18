from db.db_routine import DBRoutine

class VideoDB:
    def __init__(self, db_routine: DBRoutine):
        self.db = db_routine

    def get_all_heroes(self):
        results = self.db.execute("""
            SELECT DISTINCT hero FROM (
                SELECT hero FROM skill_heroes WHERE hero IS NOT NULL
                UNION
                SELECT hero FROM item_heroes WHERE hero IS NOT NULL
            ) ORDER BY hero
        """)
        return [row[0] for row in results]

    def get_videos(self, video_type="", status="", skill_ids=None, item_ids=None, hero_name="", sort_by="date", sort_order="DESC"):
        query = """
            SELECT v.id, v.title, v.type, v.date, v.status, v.description,
                   GROUP_CONCAT(DISTINCT s.name) as skills,
                   GROUP_CONCAT(DISTINCT i.name) as items,
                   GROUP_CONCAT(DISTINCT vh.hero_name) as heroes
            FROM videos v
            LEFT JOIN video_skills vs ON v.id = vs.video_id
            LEFT JOIN skills s ON vs.skill_id = s.id
            LEFT JOIN video_items vi ON v.id = vi.video_id
            LEFT JOIN items i ON vi.item_id = i.id
            LEFT JOIN video_heroes vh ON v.id = vh.video_id
            WHERE 1=1
        """
        params = []
        if video_type:
            query += " AND v.type = ?"
            params.append(video_type)
        if status:
            query += " AND v.status = ?"
            params.append(status)
        if skill_ids:
            query += " AND v.id IN (SELECT video_id FROM video_skills WHERE skill_id IN ({}))".format(",".join("?" * len(skill_ids)))
            params.extend(skill_ids)
        if item_ids:
            query += " AND v.id IN (SELECT video_id FROM video_items WHERE item_id IN ({}))".format(",".join("?" * len(item_ids)))
            params.extend(item_ids)
        if hero_name:
            query += " AND v.id IN (SELECT video_id FROM video_heroes WHERE hero_name LIKE ?)"
            params.append(f"%{hero_name}%")
        query += " GROUP BY v.id"
        query += f" ORDER BY v.{sort_by} {sort_order}"
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "type": row[2],
                    "date": row[3],
                    "status": row[4],
                    "description": row[5],
                    "skills": row[6] or "",
                    "items": row[7] or "",
                    "heroes": row[8] or ""
                }
                for row in cursor.fetchall()
            ]

    def add_video(self, title, video_type, date, status, description, skill_ids, item_ids, hero_names):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO videos (title, type, date, status, description) VALUES (?, ?, ?, ?, ?)",
                          (title, video_type, date, status, description))
            video_id = cursor.lastrowid
            for skill_id in skill_ids:
                cursor.execute("INSERT INTO video_skills (video_id, skill_id) VALUES (?, ?)", (video_id, skill_id))
            for item_id in item_ids:
                cursor.execute("INSERT INTO video_items (video_id, item_id) VALUES (?, ?)", (video_id, item_id))
            for hero_name in hero_names:
                cursor.execute("INSERT INTO video_heroes (video_id, hero_name) VALUES (?, ?)", (video_id, hero_name))

    def update_video(self, video_id, title, video_type, date, status, description, skill_ids, item_ids, hero_names):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE videos SET title = ?, type = ?, date = ?, status = ?, description = ? WHERE id = ?",
                          (title, video_type, date, status, description, video_id))
            cursor.execute("DELETE FROM video_skills WHERE video_id = ?", (video_id,))
            cursor.execute("DELETE FROM video_items WHERE video_id = ?", (video_id,))
            cursor.execute("DELETE FROM video_heroes WHERE video_id = ?", (video_id,))
            for skill_id in skill_ids:
                cursor.execute("INSERT INTO video_skills (video_id, skill_id) VALUES (?, ?)", (video_id, skill_id))
            for item_id in item_ids:
                cursor.execute("INSERT INTO video_items (video_id, item_id) VALUES (?, ?)", (video_id, item_id))
            for hero_name in hero_names:
                cursor.execute("INSERT INTO video_heroes (video_id, hero_name) VALUES (?, ?)", (video_id, hero_name))

    def delete_video(self, video_id):
        self.db.execute("DELETE FROM videos WHERE id = ?", (video_id,))