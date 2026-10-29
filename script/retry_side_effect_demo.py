from sqlmodel import Session, select, func
from sqlalchemy.exc import DBAPIError
from psycopg.errors import SerializationFailure

from models import User
from schemas import UserCreate
from services import transaction
from services.result import UserResult
from exceptions import UsernameExistsException
from security import hash_password
from session_factory import create_session

external_messages = []
operation_exec_count = 0
def create_user_operation(
    session: Session,
    args: list
) -> UserResult:
    assert len(args) > 0

    user_data = args[0]

    statement = select(User).where(
        User.username == user_data.username
    )
    user_get = session.exec(statement).first()
    if user_get is not None:
        raise UsernameExistsException(user_data.username)
    
    hashed_password = hash_password(user_data.password)

    user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    session.add(user)

    external_messages.append(f"user {user.username} - {user.id} created success")

    session.flush()

    global operation_exec_count
    operation_exec_count += 1
    if operation_exec_count == 1:
        raise DBAPIError(
            statement=None,
            params=None,
            orig=SerializationFailure()
        )

    assert user.id is not None

    session.refresh(user)

    return UserResult(
        user.id,
        user.username,
        user.hashed_password,
        user.is_active,
        user.role
    )


session = create_session()

user = session.exec(
    select(User).where(User.username == "atubo")
).first()
if user is not None:
    session.delete(user)
    session.commit()

users_count_old = session.exec(
    select(func.count()).select_from(User)
).one()
session.close()

session_create_count = 0
def session_factory()->Session:
    global session_create_count
    session_create_count += 1
    session = create_session()
    return session

user_data = UserCreate(
    username = "atubo",
    password = "atubo123"
)
args = [user_data]
transaction.run_transaction_with_retry(
    session_factory,
    create_user_operation,
    args,
    3
)

session_new = create_session()
users_count_new = session_new.exec(
    select(func.count()).select_from(User)
).one()
users_created_count = users_count_new - users_count_old

print("After transaction:")
print(f"operation exec count: {operation_exec_count}")
print(f"session factory created count: {session_create_count}")
print(f"table users created count: {users_created_count}")
print(f"messages len: {len(external_messages)}, messages: {external_messages}")

# 以上运行输出
# uv run python -m script.retry_side_effect_demo
# 2026-10-27 11:23:45,030 INFO sqlalchemy.engine.Engine select pg_catalog.version()
# 2026-10-27 11:23:45,031 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-27 11:23:45,036 INFO sqlalchemy.engine.Engine select current_schema()
# 2026-10-27 11:23:45,036 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-27 11:23:45,040 INFO sqlalchemy.engine.Engine show standard_conforming_strings
# 2026-10-27 11:23:45,040 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-27 11:23:45,048 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:23:45,069 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.username = %(username_1)s::VARCHAR
# 2026-10-27 11:23:45,070 INFO sqlalchemy.engine.Engine [generated in 0.00022s] {'username_1': 'atubo'}
# 2026-10-27 11:23:45,081 INFO sqlalchemy.engine.Engine SELECT orders.id AS orders_id, orders.user_id AS orders_user_id, orders.status AS orders_status 
# FROM orders 
# WHERE %(param_1)s::INTEGER = orders.user_id
# 2026-10-27 11:23:45,082 INFO sqlalchemy.engine.Engine [generated in 0.00056s] {'param_1': 8}
# 2026-10-27 11:23:45,085 INFO sqlalchemy.engine.Engine DELETE FROM users WHERE users.id = %(id)s::INTEGER
# 2026-10-27 11:23:45,085 INFO sqlalchemy.engine.Engine [generated in 0.00014s] {'id': 8}
# 2026-10-27 11:23:45,088 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-27 11:23:45,090 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:23:45,093 INFO sqlalchemy.engine.Engine SELECT count(*) AS count_1 
# FROM users
# 2026-10-27 11:23:45,093 INFO sqlalchemy.engine.Engine [generated in 0.00033s] {}
# 2026-10-27 11:23:45,097 INFO sqlalchemy.engine.Engine ROLLBACK
# 2026-10-27 11:23:45,098 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:23:45,099 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.username = %(username_1)s::VARCHAR
# 2026-10-27 11:23:45,099 INFO sqlalchemy.engine.Engine [cached since 0.02968s ago] {'username_1': 'atubo'}
# 2026-10-27 11:23:45,210 INFO sqlalchemy.engine.Engine INSERT INTO users (username, hashed_password, is_active, role) VALUES (%(username)s::VARCHAR, %(hashed_password)s::VARCHAR, %(is_active)s, %(role)s::VARCHAR) RETURNING users.id
# 2026-10-27 11:23:45,210 INFO sqlalchemy.engine.Engine [generated in 0.00051s] {'username': 'atubo', 'hashed_password': '$argon2id$v=19$m=65536,t=3,p=4$3hwHakkRuzgCts4Xs/5XGw$G5Yf8b1lGlsk+kG4Qn9MwQdep4jrC9osWS0IB75CaHE', 'is_active': True, 'role': 'customer'}
# 2026-10-27 11:23:45,212 INFO sqlalchemy.engine.Engine ROLLBACK
# 2026-10-27 11:23:45,214 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:23:45,214 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.username = %(username_1)s::VARCHAR
# 2026-10-27 11:23:45,214 INFO sqlalchemy.engine.Engine [cached since 0.1451s ago] {'username_1': 'atubo'}
# 2026-10-27 11:23:45,328 INFO sqlalchemy.engine.Engine INSERT INTO users (username, hashed_password, is_active, role) VALUES (%(username)s::VARCHAR, %(hashed_password)s::VARCHAR, %(is_active)s, %(role)s::VARCHAR) RETURNING users.id
# 2026-10-27 11:23:45,329 INFO sqlalchemy.engine.Engine [cached since 0.1192s ago] {'username': 'atubo', 'hashed_password': '$argon2id$v=19$m=65536,t=3,p=4$meGuYcJxIn7UQ+EbTzwaXg$ngMnQRGsiK3Laji9A6NRcUAP7wNlaLv3rCPYLyHRtxw', 'is_active': True, 'role': 'customer'}
# 2026-10-27 11:23:45,331 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.id = %(pk_1)s::INTEGER
# 2026-10-27 11:23:45,331 INFO sqlalchemy.engine.Engine [generated in 0.00014s] {'pk_1': 10}
# 2026-10-27 11:23:45,333 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-27 11:23:45,335 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:23:45,335 INFO sqlalchemy.engine.Engine SELECT count(*) AS count_1 
# FROM users
# 2026-10-27 11:23:45,335 INFO sqlalchemy.engine.Engine [cached since 0.2422s ago] {}
# After transaction:
# operation exec count: 2
# session factory created count: 2
# table users created count: 1
# messages len: 2, messages: ['user atubo - None created success', 'user atubo - None created success']