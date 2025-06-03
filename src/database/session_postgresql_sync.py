

from sqlalchemy.orm import Session, sessionmaker

from database.session_postgresql import sync_postgresql_engine

SyncPostgresqlSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_postgresql_engine
)


def get_sync_postgresql_session() -> Session:
    return SyncPostgresqlSessionLocal()
