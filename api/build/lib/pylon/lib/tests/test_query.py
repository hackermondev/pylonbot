import pytest
from pydantic import ValidationError
from pylon.lib.query import Query
from typing import Optional

from datetime import datetime
from pylon.database import Model, ModelNotFound
from pylon.models.user import User


class ExampleModel(Model):
    class Meta:
        table_name = "test"

    a: int
    b: Optional[str]
    c: bool


async def test_compile_select_query():
    test_model_query = Query(ExampleModel).select().where("a = {.a}").fetchone()
    assert test_model_query.sql == "SELECT a, b, c FROM test WHERE a = $1 LIMIT 1"
    assert callable(test_model_query.build())


async def test_compile_insert_query():
    test_model_query = Query(ExampleModel).insert()
    assert test_model_query.sql == "INSERT INTO test (a, b, c) VALUES ($1, $2, $3)"
    assert callable(test_model_query.build())


async def test_compile_delete_query():
    test_model_query = Query(ExampleModel).delete().where("a = {.a}")
    assert test_model_query.sql == "DELETE FROM test WHERE a = $1"
    assert callable(test_model_query.build())


async def test_compile_update_query():
    test_model_query = Query(ExampleModel).update("b", "a", "c").where("a = {.a}")
    assert test_model_query.sql == "UPDATE test SET b = $1, a = $2, c = $3 WHERE a = $2"
    assert callable(test_model_query.build())


async def test_validate_select_query(conn, user: User):
    test_select_user_query = Query(User).select().where("id = {.id}").fetchone()
    with pytest.raises(ValidationError):
        await test_select_user_query.build()(conn, id="fuck")


async def test_execute_select_query(conn, user: User):
    test_select_user_query = Query(User).select().where("id = {.id}").fetchone()
    assert (
        test_select_user_query.sql
        == "SELECT id, email, password, last_seen_at FROM users WHERE id = $1 LIMIT 1"
    )
    assert (await test_select_user_query.build()(conn, id=user.id)).id == user.id


async def test_execute_insert_query(conn, snowflake):
    test_insert_user_query = Query(User).insert()
    assert (
        test_insert_user_query.sql
        == "INSERT INTO users (id, email, password, last_seen_at) VALUES ($1, $2, $3, $4)"
    )
    user_id = await snowflake()
    await test_insert_user_query.build()(
        conn, user=User(id=user_id, last_seen_at=datetime.utcnow())
    )


async def test_execute_delete_query(conn, user):
    test_delete_user_query = Query(User).delete().where("id = {.id}")
    assert test_delete_user_query.sql == "DELETE FROM users WHERE id = $1"

    await test_delete_user_query.build()(
        conn, id=user.id,
    )

    with pytest.raises(ModelNotFound):
        await Query(User).select().where("id = {.id}").fetchone().build()(
            conn, id=user.id
        )


async def test_execute_update_query(conn, user):
    test_update_user_query = Query(User).update("last_seen_at").where("id = {.id}")
    assert (
        test_update_user_query.sql == "UPDATE users SET last_seen_at = $1 WHERE id = $2"
    )

    now = datetime.utcnow()
    await test_update_user_query.build()(conn, id=user.id, last_seen_at=now)

    user = (
        await Query(User)
        .select()
        .where("id = {.id}")
        .fetchone()
        .build()(conn, id=user.id)
    )
    assert user.last_seen_at.replace(tzinfo=None) == now


async def test_execute_update_with_optional_field(conn, user):
    test_update_user_query = Query(User).update("email").where("id = {.id}")
    assert test_update_user_query.sql == "UPDATE users SET email = $1 WHERE id = $2"

    await test_update_user_query.build()(conn, id=user.id, email=None)

    user = (
        await Query(User)
        .select()
        .where("id = {.id}")
        .fetchone()
        .build()(conn, id=user.id)
    )
    assert user.email is None
