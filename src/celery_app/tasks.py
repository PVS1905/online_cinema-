from database.models.accounts import TokenBaseModel
from .worker import celery_src
from ..database.session_postgresql_sync import get_sync_postgresql_session
from datetime import datetime


@celery_src.task
def delete_expired_tokens():

    db = get_sync_postgresql_session()

    try:
        expired_tokens = db.query(TokenBaseModel).filter(
            TokenBaseModel.expires_at < datetime.utcnow()
        ).all()

        for token in expired_tokens:
            db.delete(token)

        db.commit()
        return f"Deleted {len(expired_tokens)} tokens"
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
