import logging

import sanic
from sanic.log import logger

from pylon.config import config


class SanicSentry:
    def __init__(self, app=None):
        self.app = None
        self.handler = None
        self.client = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: sanic.Sanic):
        if not config.sentry_dsn:
            logger.warning("Not enabling sentry as no SENTRY_DSN was provided")
            return

        self.client = raven.Client(
            dsn=config.sentry_dsn,
            transport=raven_aiohttp.AioHttpTransport,
            environment=config.environment,
        )
        self.handler = SentryHandler(client=self.client, level=logging.WARNING)
        logger.addHandler(self.handler)

        # This is noisy in production
        raven.breadcrumbs.ignore_logger("hypercorn.access")

        self.app = app
        self.app.sentry = self
