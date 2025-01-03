import asyncpg
import simplejson
import functools

from pydantic import BaseModel


async def create_connection_pool(dsn):
    return await asyncpg.create_pool(dsn=dsn)


def _to_table_name(model_cls):
    return model_cls.Meta.table_name


class ModelNotFound(Exception):
    pass


class ModelValidationError(Exception):
    pass


class Model(BaseModel):
    class Config:
        json_dumps = functools.partial(simplejson.dumps, bigint_as_string=True)
