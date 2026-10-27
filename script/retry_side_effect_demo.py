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

    global operation_exec_count
    operation_exec_count += 1
    if operation_exec_count == 1:
        raise DBAPIError(
            statement=None,
            params=None,
            orig=SerializationFailure()
        )

    session.flush()

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

user_data = UserCreate(
    username = "atubo",
    password = "atubo123"
)
args = [user_data]
transaction.run_transaction(
    create_session,
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
print(f"table users created count: {users_created_count}")
print(f"messages len: {len(external_messages)}, messages: {external_messages}")

# 以上运行输出
# uv run python -m script.retry_side_effect_demo
# 2026-10-27 11:16:37,868 INFO sqlalchemy.engine.Engine select pg_catalog.version()
# 2026-10-27 11:16:37,869 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-27 11:16:37,872 INFO sqlalchemy.engine.Engine select current_schema()
# 2026-10-27 11:16:37,872 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-27 11:16:37,875 INFO sqlalchemy.engine.Engine show standard_conforming_strings
# 2026-10-27 11:16:37,875 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-27 11:16:37,881 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:16:37,904 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.username = %(username_1)s::VARCHAR
# 2026-10-27 11:16:37,904 INFO sqlalchemy.engine.Engine [generated in 0.00060s] {'username_1': 'atubo'}
# 2026-10-27 11:16:37,914 INFO sqlalchemy.engine.Engine SELECT orders.id AS orders_id, orders.user_id AS orders_user_id, orders.status AS orders_status 
# FROM orders 
# WHERE %(param_1)s::INTEGER = orders.user_id
# 2026-10-27 11:16:37,914 INFO sqlalchemy.engine.Engine [generated in 0.00050s] {'param_1': 7}
# 2026-10-27 11:16:37,918 INFO sqlalchemy.engine.Engine DELETE FROM users WHERE users.id = %(id)s::INTEGER
# 2026-10-27 11:16:37,918 INFO sqlalchemy.engine.Engine [generated in 0.00031s] {'id': 7}
# 2026-10-27 11:16:37,920 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-27 11:16:37,923 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:16:37,925 INFO sqlalchemy.engine.Engine SELECT count(*) AS count_1 
# FROM users
# 2026-10-27 11:16:37,926 INFO sqlalchemy.engine.Engine [generated in 0.00036s] {}
# 2026-10-27 11:16:37,928 INFO sqlalchemy.engine.Engine ROLLBACK
# 2026-10-27 11:16:37,929 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:16:37,929 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.username = %(username_1)s::VARCHAR
# 2026-10-27 11:16:37,929 INFO sqlalchemy.engine.Engine [cached since 0.0257s ago] {'username_1': 'atubo'}
# 2026-10-27 11:16:38,040 INFO sqlalchemy.engine.Engine ROLLBACK
# 2026-10-27 11:16:38,042 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:16:38,042 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.username = %(username_1)s::VARCHAR
# 2026-10-27 11:16:38,042 INFO sqlalchemy.engine.Engine [cached since 0.1385s ago] {'username_1': 'atubo'}
# 2026-10-27 11:16:38,161 INFO sqlalchemy.engine.Engine INSERT INTO users (username, hashed_password, is_active, role) VALUES (%(username)s::VARCHAR, %(hashed_password)s::VARCHAR, %(is_active)s, %(role)s::VARCHAR) RETURNING users.id
# 2026-10-27 11:16:38,161 INFO sqlalchemy.engine.Engine [generated in 0.00086s] {'username': 'atubo', 'hashed_password': '$argon2id$v=19$m=65536,t=3,p=4$wFqPL2Z6KFT1ybO6DrKvZg$Ffyho9pGOP3uhWtwLOckCbsrx/fuh2C7Ns2p92c9Paw', 'is_active': True, 'role': 'customer'}
# 2026-10-27 11:16:38,166 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.id = %(pk_1)s::INTEGER
# 2026-10-27 11:16:38,167 INFO sqlalchemy.engine.Engine [generated in 0.00039s] {'pk_1': 8}
# 2026-10-27 11:16:38,169 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-27 11:16:38,171 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-27 11:16:38,172 INFO sqlalchemy.engine.Engine SELECT count(*) AS count_1 
# FROM users
# 2026-10-27 11:16:38,172 INFO sqlalchemy.engine.Engine [cached since 0.247s ago] {}
# After transaction:
# operation exec count: 2
# table users created count: 1
# messages len: 2, messages: ['user atubo - None created success', 'user atubo - None created success']