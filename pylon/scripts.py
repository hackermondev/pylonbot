from pylon.lib.query import Query
from pylon.server import app, log
from pylon.models.deployment import GuildDeployment


get_all_deployments_raw = Query(GuildDeployment).select().preper().build()


async def write_all_deployments_to_etcd():
    async with app.db.acquire() as conn:
        query = await get_all_deployments_raw(conn)

        async with conn.transaction():
            async for record in query.cursor():
                deployment = GuildDeployment.parse_obj(dict(record))

                try:
                    await deployment.publish()
                    log.info(f"Republished deployment {deployment.id} to etcd")
                except Exception:
                    log.exception(
                        f"Failed to republish deployment {deployment.id} to etcd (skippin): "
                    )
