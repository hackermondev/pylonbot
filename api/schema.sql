CREATE TABLE IF NOT EXISTS users (
    id bigserial NOT NULL PRIMARY KEY,
    email text,
    PASSWORD text,
    last_seen_at timestamp WITH time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_connected_accounts (
    id bigserial NOT NULL PRIMARY KEY,
    user_id bigint,
    last_authed_at timestamp WITH time zone DEFAULT now(),
    provider text,
    provider_id text,
    provider_name text,
    provider_avatar text,
    provider_token text
);

CREATE TABLE IF NOT EXISTS bots (
    id bigserial NOT NULL PRIMARY KEY,
    bot_token text,
    client_id text,
    client_secret text,
    user_id bigint REFERENCES users
);

CREATE TABLE IF NOT EXISTS guilds (
    id bigserial NOT NULL,
    user_id bigint REFERENCES users,
    PRIMARY KEY (id, user_id)
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id bigserial NOT NULL PRIMARY KEY,
    user_id bigint,
    ip bigint,
    last_seen_at timestamp WITH time zone DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scripts (
    id bigserial NOT NULL PRIMARY KEY,
    bot_id bigint,
    guild_id bigint,
    user_id bigint,
    contents text,
    project text
);

CREATE TABLE IF NOT EXISTS guild_deployments (
    "id" BIGINT NOT NULL,
    "bot_id" BIGINT NOT NULL,
    "guild_id" BIGINT NOT NULL,
    "type" SMALLINT NOT NULL,
    "status" SMALLINT NOT NULL,
    "name" VARCHAR(32) NOT NULL,
    "app_id" BIGINT NULL,
    "script_id" BIGINT NULL,
    "last_updated_at" TIMESTAMP NULL,
    "config" TEXT NOT NULL,
    revision INT NOT NULL,

    PRIMARY KEY ("id", "bot_id", "guild_id")
);

CREATE INDEX IF NOT EXISTS guild_deployments_bot_id_guild_id ON guild_deployments (bot_id, guild_id);

ALTER TABLE guild_deployments ADD COLUMN IF NOT EXISTS revision INT NOT NULL DEFAULT 0;

ALTER TABLE scripts DROP COLUMN IF EXISTS config;
ALTER TABLE scripts DROP COLUMN IF EXISTS is_draft;