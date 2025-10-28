from sqlalchemy import create_engine
from db.config import PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE

def get_engine():
    engine = create_engine(
        f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DATABASE}"
    )
    return engine