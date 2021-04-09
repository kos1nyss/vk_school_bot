import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

SqlAlchemyBase = declarative_base()
__factory = None


def global_init(db_name):
    global __factory

    if __factory:
        return

    if not db_name or not db_name.strip():
        return

    connect_str = f'postgresql://postgres:Kostya@localhost:5432/{db_name}'

    engine = sqlalchemy.create_engine(connect_str, echo=False)
    __factory = sqlalchemy.orm.sessionmaker(bind=engine)

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session():
    global __factory
    return __factory()
