# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

TOTPBot is a Discord bot that manages TOTP (Time-based One-Time Password) authentication for Discord servers. It allows authorized users to generate TOTP codes and tracks their usage.

## Commands

### Running the bot
```bash
python main.py
```

### Database migrations (Alembic)
```bash
# Create a new migration
alembic revision --autogenerate -m "migration message"

# Apply migrations
alembic upgrade head

# Downgrade to previous version
alembic downgrade -1
```

### Installing dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Core Components

1. **main.py**: Entry point containing Discord bot logic and slash commands
   - `/totp`: Generate a TOTP code (requires authorized role)
   - `/show`: Display TOTP generation history
   - `/set_token`: Set TOTP token for a guild (owner only)
   - `/delete_token`: Remove TOTP token (owner only)
   - `/set_role`: Configure authorized roles (owner only)
   - `/delete_role`: Remove authorized roles (owner only)
   - `/shutdown`: Shutdown the bot (owner only)

2. **Database Layer**
   - SQLAlchemy ORM with SQLite database (TOTPlog.db)
   - Models in `models/`: Guild, Role, TOTPToken, TOTPlog
   - Database session management in `db/db.py`
   - Alembic for schema migrations

3. **Authentication System**
   - Owner-based authentication: Only OWNER_ID can manage tokens and roles
   - Role-based authentication: Users with configured roles can generate TOTP codes
   - If no roles are configured for a guild, all users can generate codes

### Key Design Patterns

- TOTP tokens are stored per guild (Discord server)
- All TOTP generations are logged with user info and timestamp
- Commands use Discord's slash command system with ephemeral responses for sensitive data
- The bot waits for new TOTP cycle if remaining time is ≤5 seconds

### Environment Configuration

Create a `.env` file from `.env.template`:
- `BOT_TOKEN`: Discord bot token
- `OWNER_ID`: Discord user ID of the bot owner