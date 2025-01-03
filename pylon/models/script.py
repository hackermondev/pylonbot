from pylon.database import Model
from pylon.lib.query import Query


class Script(Model):
    class Meta:
        table_name = "scripts"

    id: int
    bot_id: int
    guild_id: int
    user_id: int
    contents: str
    project: str


class ScriptQueries:
    create = Query(Script).insert().build()

    get_one = Query(Script).select().where("id = {.id}").fetchone().build()
