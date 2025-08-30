# 🪙 Telegram FlipCoin Game

A simple game on Telegram Gaming Platform where players place bets, flip a coin, and win (or lose 🙃).

## 🎮 Demo

*Watch the game in action!*

<div align="center">
<video src="https://github.com/user-attachments/assets/7c53809e-4242-4568-a4de-3de18d7c0f10"
       width="250" controls muted playsinline></video>
</div>


## 📁 Project Structure

```
├── app/                 # Shared models and game logic
├── services/
│   ├── api/            # FastAPI backend service
│   └── bot/            # Telegram bot service
├── web/                # Game frontend page
└── infra/              # Caddy configuration
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Game and Inline Bot configuration (from [@BotFather](https://t.me/botfather))
- Domain name (for HTTPS)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd do-dep
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Configure environment variables**
   ```env
   # Telegram Bot
   BOT_TOKEN=your_bot_token_here
   GAME_URL=https://yourdomain.com
   GAME_SHORT_NAME=your_game_name
   
   # JWT Secrets
   JWT_SECRET=your_jwt_secret
   API_JWT_SECRET=your_api_jwt_secret
   
   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=flipcoin_game
   
   # Game Settings
   INITIAL_BALANCE=1000
   JACKPOT_MULTIPLIER=2.0
   
   # ACME Email for SSL
   ACME_EMAIL=your_email@domain.com
   ```

### Running the Application

1. **Start all services**
   ```bash
   docker-compose up -d
   ```

2. **Initialize database** (first time only)
   ```bash
   docker-compose exec api python -m app.init_db
   ```

3. **Access services**
   - **Game**: https://yourdomain.com
   - **Adminer**: http://localhost:8580 (database management)
   - **API**: Available through Caddy reverse proxy
