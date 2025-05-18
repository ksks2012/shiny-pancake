import sqlite3
import logging
from contextlib import contextmanager
from utils.config import DATABASE_PATH

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DBRoutine:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            raise
        finally:
            conn.commit()
            conn.close()

    def execute(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def initialize_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Create tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    date TEXT,
                    status TEXT,
                    description TEXT,
                    local_path TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_skills (
                    video_id INTEGER,
                    skill_id INTEGER,
                    PRIMARY KEY (video_id, skill_id),
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                    FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_items (
                    video_id INTEGER,
                    item_id INTEGER,
                    PRIMARY KEY (video_id, item_id),
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_heroes (
                    video_id INTEGER,
                    hero_name TEXT,
                    PRIMARY KEY (video_id, hero_name),
                    FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
                )
            """)
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_name ON skills(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_rarity ON skill_rarities(rarity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_type ON skill_types(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill_hero ON skill_heroes(hero)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_name ON items(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_size ON items(size)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_rarity ON item_rarities(rarity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_type ON item_types(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_hero ON item_heroes(hero)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_enchantment_item_id ON enchantments(item_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_date ON videos(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_skills ON video_skills(video_id, skill_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_items ON video_items(video_id, item_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_heroes ON video_heroes(video_id, hero_name)")