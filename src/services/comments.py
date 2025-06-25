# src/services/comments.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException


from database.models.movies import Comment, CommentLike, Notification
from database.models.accounts import User




async def create_reply(comment_id: int, content: str, user: User, db: AsyncSession):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    reply = Comment(
        content=content,
        user_id=user.id,
        parent_id=comment.id,
        movie_id=comment.movie_id
    )
    db.add(reply)

    if comment.user_id != user.id:
        notification = Notification(
            recipient_id=comment.user_id,
            message=f"User {user} replied to your movie comment.",
        )
        db.add(notification)

    await db.commit()
    return reply


async def like_comment(comment_id: int, user: User, db: AsyncSession):
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    like = CommentLike(user_id=user.id, comment_id=comment_id)
    db.add(like)

    if comment.user_id != user.id:
        notification = Notification(
            recipient_id=comment.user_id,
            message=f"User {user} liked your comment.",
        )
        db.add(notification)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
