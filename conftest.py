from unipath import Path

ROOT_PATH = Path(__file__).parent


def pytest_sessionstart():
    from pytest import config
    if not hasattr(config, 'slaveinput'):
        from pyramid.paster import get_appsettings
        from sqlalchemy import engine_from_config
        from scrom.models import DBSession, Base

        config_uri = Path(ROOT_PATH, 'test.ini')
        settings = get_appsettings(config_uri)
        engine = engine_from_config(settings, 'sqlalchemy.')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine)

