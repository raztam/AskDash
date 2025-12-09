# AskDash

AI-Powered SQL Exploration Tool - Ask questions about your data in natural language.

![AskDash Screenshot](docs/screenshot.png)

## Features

- 🔌 **Multi-Database Support**: Connect PostgreSQL, MySQL, SQLite, MariaDB, and SQL Server
- 💬 **Natural Language Queries**: Ask questions about your data in plain English
- 🤖 **Multiple LLM Providers**: Supports Ollama (local), OpenAI, and Anthropic
- 📊 **Automatic Visualizations**: Smart chart suggestions (bar, line, pie, scatter)
- 🔒 **Table-Level Permissions**: Fine-grained access control for shared databases
- 📱 **Modern UI**: Clean, responsive interface with real-time chat

## Tech Stack

### Backend
- Python 3.10+
- Django 4.2
- Django REST Framework
- JWT Authentication
- SQLAlchemy-style database connectors

### Frontend
- React 18
- TypeScript
- Vite
- TailwindCSS
- Recharts
- Zustand (state management)

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- One of: Ollama (local), OpenAI API key, or Anthropic API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start server
python manage.py runserver
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file (optional for development)
cp .env.example .env

# Start development server
npm run dev
```

### Using Ollama (Local LLM)

1. Install Ollama: https://ollama.ai
2. Pull a model:
   ```bash
   ollama pull llama3.2
   ```
3. Ensure Ollama is running (it starts automatically on install)
4. Set in backend `.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   ```

### Using OpenAI

1. Get an API key from https://platform.openai.com
2. Set in backend `.env`:
   ```
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-4
   ```

### Using Anthropic (Claude)

1. Get an API key from https://console.anthropic.com
2. Set in backend `.env`:
   ```
   LLM_PROVIDER=anthropic
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
   ```

## Usage

1. Open http://localhost:3000 in your browser
2. Register a new account or login
3. Click "Add Database" to connect your first database
4. Start asking questions!

### Example Questions

- "What are the top 10 customers by total revenue?"
- "Show me the monthly sales trend for 2024"
- "How many orders were placed last week?"
- "What's the average order value by product category?"

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (get JWT tokens)
- `POST /api/auth/refresh/` - Refresh access token
- `GET /api/auth/user/` - Get current user info

### Databases
- `GET /api/databases/` - List user's databases
- `POST /api/databases/` - Create new connection
- `GET /api/databases/{id}/` - Get database details
- `DELETE /api/databases/{id}/` - Delete connection
- `POST /api/databases/{id}/test/` - Test connection
- `POST /api/databases/{id}/refresh_schema/` - Refresh schema
- `GET /api/databases/{id}/tables/` - List accessible tables

### Permissions
- `GET /api/permissions/by_database/?database_id=X` - Get permissions
- `POST /api/permissions/grant/` - Grant permission
- `POST /api/permissions/revoke/` - Revoke permission

### Chat
- `GET /api/sessions/` - List chat sessions
- `POST /api/sessions/` - Create new session
- `GET /api/sessions/{id}/` - Get session with messages
- `DELETE /api/sessions/{id}/` - Delete session
- `POST /api/ask/` - Ask a question

## Project Structure

```
AskDashv2/
├── backend/
│   ├── askdash/           # Django project settings
│   ├── api/               # Main API app
│   │   ├── models.py      # Database models
│   │   ├── views.py       # API views
│   │   ├── serializers.py # DRF serializers
│   │   ├── permissions.py # Custom permissions
│   │   ├── urls.py        # URL routing
│   │   ├── utils/         # Utilities
│   │   │   ├── db_connector.py     # Database connections
│   │   │   ├── schema_extractor.py # Schema extraction
│   │   │   └── sql_executor.py     # Safe SQL execution
│   │   └── services/      # LLM services
│   │       ├── prompts.py      # Prompt templates
│   │       ├── llm_base.py     # Base LLM class
│   │       ├── llm_ollama.py   # Ollama adapter
│   │       ├── llm_openai.py   # OpenAI adapter
│   │       ├── llm_anthropic.py# Anthropic adapter
│   │       └── llm_factory.py  # Service factory
│   ├── manage.py
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/    # React components
    │   ├── pages/         # Page components
    │   ├── services/      # API services
    │   ├── store/         # Zustand stores
    │   ├── types/         # TypeScript types
    │   ├── App.tsx        # Main app component
    │   └── main.tsx       # Entry point
    ├── package.json
    └── vite.config.ts
```

## Security Notes

1. **Change default secrets**: Always update `DJANGO_SECRET_KEY` and `ENCRYPTION_KEY` in production
2. **Database passwords**: Stored encrypted using Fernet symmetric encryption
3. **SQL injection**: Queries are validated and parameterized
4. **Permission system**: Table-level access control prevents unauthorized data access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.
