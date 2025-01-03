from sanic import Blueprint  # , response

# from sanic.response import HTTPResponse
# from sanic.request import Request


kv_blueprint = Blueprint("kv")

# GET /guilds/<guild_id>/kv/namespaces
# DELETE /guilds/<guild_id/kv/namespaces/<namespace>
# GET /guilds/<guild_id/kv/namespaces/<namespace>/keys
# GET /guilds/<guild_id/kv/namespaces/<namespace>/keys/<key>
# PUT /guilds/<guild_id/kv/namespaces/<namespace>/keys/<key>
# DELETE /guilds/<guild_id>/kv/namespaces/<namespace>/keys/<key>
