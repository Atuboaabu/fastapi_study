from sqlmodel import create_engine, SQLModel
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import event
import models
from config import settings


engine = create_engine(
    settings.database_url,
    echo=settings.sql_echo,
)
