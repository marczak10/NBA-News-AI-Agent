from app.database.table_models import Base

def create_tables(engine):
    Base.metadata.create_all(engine)