
from sqlmodel import create_engine, Session, text
from sqlalchemy import event
from sqlalchemy.exc import TimeoutError

from config import settings

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0,
    pool_timeout = 2
)

@event.listens_for(demo_engine, "connect")
def connect_check(dpapiconnection, connection_record):
    print("Demo Engine Connected")

@event.listens_for(demo_engine, "checkout")
def checkout_check(dpapiconnection, connection_record, connection_proxy):
    print("Demo Engine Checkout")

@event.listens_for(demo_engine, "checkin")
def checkin_check(dpapiconnection, connection_record):
    print("Demo Engine Checkin")

with Session(demo_engine) as session:
    session.execute(text("SELECT 1"))

with Session(demo_engine) as session1:
    session1.execute(text("SELECT 1"))

with Session(demo_engine) as session:
    session.execute(text("SELECT 1"))

session1 = Session(demo_engine)
session2 = Session(demo_engine)
session3 = Session(demo_engine)

try:
    session1.execute(text("SELECT 1"))
    session2.execute(text("SELECT 1"))
    session3.execute(text("SELECT 1"))
except TimeoutError:
    print("pool connection timeout")
finally:
    session1.close()
    session2.close()
    session3.close()

### 执行输出
# uv run python -m script.pool_demo
# Demo Engine Connected
# Demo Engine Checkout
# Demo Engine Checkin
# Demo Engine Checkout
# Demo Engine Checkin
# Demo Engine Checkout
# Demo Engine Checkin
# Demo Engine Checkout
# Demo Engine Connected
# Demo Engine Checkout
# pool connection timeout
# Demo Engine Checkin
# Demo Engine Checkin
###