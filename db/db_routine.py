import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.config import DATABASE_PATH
from db.models import Base

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DBRoutine:
    def __init__(self):
        self.db_path = f"sqlite:///{DATABASE_PATH}"
        self.engine = create_engine(self.db_path, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.initialize_database()

    @contextmanager
    def get_connection(self):
        """Provide a SQLAlchemy session as a context manager."""
        session = self.Session()
        try:
            yield session
        except Exception as e:
            logger.error(f"Database error: {e}")
            session.rollback()
            raise
        finally:
            session.commit()
            session.close()

    def execute(self, query, params=()):
        """Execute a raw SQL query and return results as a list of dictionaries."""
        with self.get_connection() as session:
            try:
                result = session.execute(query, params)
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return []
            except Exception as e:
                logger.error(f"Query execution failed: {query}, error: {e}")
                raise

    def initialize_database(self):
        """Create tables and indexes defined in models."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise