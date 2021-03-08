# Anon Talks

A Telegram bot for anonymous conversations.

## Development environment

It's recommended to use Docker and Docker-compose for local development.

Setup environment variables. You can copy it manually from examples.
```bash
cp envs/bot/example.env envs/bot/.env
cp envs/db/example.env envs/db/.env
```

Build docker images:
```bash
docker-compose build
```
and then run services:
```bash
docker-compose up -d
```

## Initialize database
To create db tables, use `main.py` script in the next way:
```bash
python main.py syncdb
```
## Telegram API integration

The bot uses webhooks. For proper work of Telegram bot API, provide next environment variables:
```
BOT_API_TOKEN=
```
where
- `BOT_API_TOKEN` is a bot token, provided by BotFather

## License
The MIT License (MIT)

Contributed by [Campos Ilya](https://github.com/EliasCampos)
