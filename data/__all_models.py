import sqlalchemy
from .db_session import SqlAlchemyBase


class Admin(SqlAlchemyBase):
    __tablename__ = 'admins'

    vk_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    status = sqlalchemy.Column(sqlalchemy.Integer)


class Event(SqlAlchemyBase):
    __tablename__ = 'events'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    owner = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('admins.vk_id'),
                              nullable=True)
    post_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    time_from = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    time_to = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    is_added = sqlalchemy.Column(sqlalchemy.Boolean, nullable=False)


class Key(SqlAlchemyBase):
    __tablename__ = 'keys'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    key = sqlalchemy.Column(sqlalchemy.String)
