from pylon.database import Model
from pylon.lib.query import Query


class Bot(Model):
    class Meta:
        table_name = "bots"

    id: int
    bot_token: str
    client_id: str
    client_secret: str
    user_id: int


class BotQueries:
    get_one = Query(Bot).select().where("id = {.id}").fetchone().build()

    create = Query(Bot).insert().build()
