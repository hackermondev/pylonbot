from pylon.lib.shardclient import shardclient

PERMISSION_MANAGE_SERVER = 0x00000020


class GuildHelper:
    @staticmethod
    async def can_manage(guild_id: int, guild_member_discord_id: int) -> bool:
        member = await shardclient.get_guild_member(guild_id, guild_member_discord_id)
        if member is None:
            return False

        return (
            member["permissions"] & PERMISSION_MANAGE_SERVER == PERMISSION_MANAGE_SERVER
        )
