from pylon.database import Model
from pylon.lib.query import Query


class Guild(Model):
    class Meta:
        table_name = "guilds"

    id: int
    user_id: int


class GuildQueries:
    get_one = Query(Guild).select().where("id = {.id}").fetchone().build()

    get_for_user_id = (
        Query(Guild).select().where("user_id = {.user_id}").fetchall().build()
    )

    create = Query(Guild).insert().build()
