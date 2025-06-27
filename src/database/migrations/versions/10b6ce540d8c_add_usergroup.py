"""Add usergroup

Revision ID: 10b6ce540d8c
Revises: 1c9d8fe6a4ea
Create Date: 2025-06-23 15:40:06.240747
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select
from sqlalchemy import String

# revision identifiers, used by Alembic.
revision: str = '10b6ce540d8c'
down_revision: Union[str, None] = '1c9d8fe6a4ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#
# def upgrade():
#     # Створення таблиці groups
#     op.create_table(
#         'groups',
#         sa.Column('id', sa.Integer, primary_key=True),
#         sa.Column('name', sa.String, nullable=False, unique=True)
#     )
#
#     # Псевдотаблиця для вставки
#     groups_table = table('groups',
#                          column('id', sa.Integer),
#                          column('name', String))
#
#     conn = op.get_bind()
#
#     # Перевіряємо, чи є запис
#     result = conn.execute(
#         select(groups_table.c.id).where(groups_table.c.name == 'user')
#     ).fetchone()
#
#     # Якщо немає — додаємо
#     if result is None:
#         op.bulk_insert(groups_table, [{"name": "user"}])
#
#
# def downgrade():
#     # Видаляємо таблицю повністю (і разом з нею — запис 'USER')
#     op.drop_table('groups')

def upgrade():
    op.execute("INSERT INTO user_groups (name) VALUES ('USER');")
    op.execute("INSERT INTO user_groups (name) VALUES ('ADMIN');")
    op.execute("INSERT INTO user_groups (name) VALUES ('MODERATOR');")

def downgrade():
    op.execute("DELETE FROM user_groups WHERE name = 'USER';")
    op.execute("DELETE FROM user_groups WHERE name = 'ADMIN';")
    op.execute("DELETE FROM user_groups WHERE name = 'MODERATOR';")
