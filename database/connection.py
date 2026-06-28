from sqlalchemy import create_engine
from core.settings import settings
from sqlalchemy.orm import sessionmaker


engine = create_engine(settings.database_url, pool_pre_ping=True)

LocalSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = LocalSession()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()