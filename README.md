# ChatDebBot

ChatDebBot is a WhatsApp chatbot designed to help individuals and small business owners manage informal debt collection and payment reminders.

It aims to simplify the process of tracking money owed by customers, monitoring outstanding payments, and sending automated reminders directly through WhatsApp, without requiring a complex management system.

The project is built with Python and FastAPI, using the official WhatsApp Cloud API by Meta for messaging and SQLite for data persistence.

**Current status:** Under development.

## User manual

See the [user manual](./MANUAL_USUARIO.md) to learn how to create, list, and
track charges through WhatsApp.

## Running with Docker

Copy the environment variable template and fill in your WhatsApp API values:

```bash
cp .env.example .env
```

Start the bot:

```bash
docker compose up -d --build
```

The webhook will be available at `http://localhost:8000/webhook`. SQLite data
will be persisted in the `data/` directory.

To view the logs:

```bash
docker compose logs -f bot
```

To stop the bot:

```bash
docker compose down
```

## Running the tests

The unit tests use Python's standard library:

```bash
.venv/bin/python -m unittest discover -s tests -v
```