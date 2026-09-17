from sqlmodel import create_engine, SQLModel
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import event
import models
from config import settings

connect_args = {
    "check_same_thread": False
}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=settings.sql_echo,
)

@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection,
    connection_record,
):
    cursor = dbapi_connection.cursor()
    cursor.execute(
        "PRAGMA foreign_keys=ON"
    )
    cursor.close()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield