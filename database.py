from sqlmodel import create_engine, SQLModel
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import event

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {
    "check_same_thread": False
}

engine = create_engine(
    sqlite_url,
    connect_args=connect_args,
    echo=True,
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