from sqlalchemy import create_engine
from sqlalchemy.orm.session import sessionmaker


def session_creator():
    engine = create_engine("sqlite:///database2.db", connect_args={'check_same_thread': False})
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

