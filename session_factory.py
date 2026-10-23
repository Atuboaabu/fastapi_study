
from collections.abc import Callable
from sqlmodel import Session

SessionFactory = Callable[[], Session]

