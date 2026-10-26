from collections.abc import Callable
from sqlmodel import Session
from database import engine

SessionFactory = Callable[[], Session]

def create_session()->Session:
    return Session(engine)