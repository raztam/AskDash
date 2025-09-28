# AskDash - AI-Powered Database Dashboard

A plug-and-play AI dashboard that connects to any existing web store or database and allows users to interact with their data using natural language queries. The system converts English queries into SQL, executes them, and generates dynamic visualizations.

## 🌟 Features

### Natural Language Queries

- Users type questions like "Show total orders per customer last month"
- AI generates SQL queries based on the connected database schema

### Flexible AI Integration

- **OpenAI GPT Models**: Use OpenAI's powerful language models (GPT-3.5, GPT-4)
- **Local AI Models**: Run completely offline with LM Studio and local models
- **Privacy-First**: Choose between cloud AI or local processing based on your needs

### Dynamic Visualizations

- Automatically chooses chart type based on query results:
  - Numeric → KPI card
  - Time series → Line chart
  - Categories → Bar/Pie chart

### Chat-Like Interface

- All past queries stored in chat history
- Users can revisit, rerun, or edit queries
- Sidebar shows all previous queries like an AI chat

### Schema-Aware AI

- Dashboard reads database schema once on connection
- Schema stored and reused for AI SQL generation
- Updated only when the database changes

### Database Agnostic

- Supports MySQL, PostgreSQL, MariaDB, SQLite
- Users provide read-only credentials
- Sandbox ensures no modifications are possible

### Privacy & Security

- Read-only access enforced at the connection level
- Query results processed securely
- No data stored or shared without user consent

## 🏗️ Architecture

### Backend (Python FastAPI)

- **FastAPI** for high-performance API endpoints
- **SQLAlchemy** for database abstraction and ORM
- **OpenAI API** or **Local AI Models** for natural language to SQL conversion
- **Pandas** for data processing and analysis

### Frontend (React TypeScript)

- **Material-UI** for modern, responsive design
- **Recharts** for data visualization
- **Axios** for API communication
- **TypeScript** for type safety

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- AI Provider: Either OpenAI API key OR LM Studio with a local model

### AI Configuration Options

AskDash supports multiple AI providers:

1. **OpenAI (Cloud)**: Uses OpenAI's GPT models - requires API key and internet
2. **LM Studio (Local)**: Run models locally - complete privacy, no internet required
3. **Other OpenAI-Compatible APIs**: Works with most OpenAI-compatible endpoints

For **Local AI setup with LM Studio**, see our detailed guide: [LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md)

### Backend Setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:

   ```bash
   cp .env.example .env
   ```

5. Configure your AI provider in `.env`:

   **For OpenAI:**
   ```bash
   AI_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   **For LM Studio:**
   ```bash
   AI_PROVIDER=lmstudio
   LM_STUDIO_BASE_URL=http://localhost:1234/v1
   LM_STUDIO_MODEL=local-model
   ```

   See [LM_STUDIO_SETUP.md](LM_STUDIO_SETUP.md) for detailed local AI setup instructions.

6. Start the backend server:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`

### Frontend Setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The frontend will be available at `http://localhost:3000`

## 📖 Usage

1. **Connect to Database**: Click "Add Database" and provide your database connection details
2. **Ask Questions**: Use natural language to query your data (e.g., "Show sales by month")
3. **View Results**: See automatically generated visualizations
4. **Explore History**: Review and rerun past queries from the sidebar

### Example Queries

- "Show total revenue by product category"
- "What are the top 10 customers by order value?"
- "Display monthly user registrations for the last year"
- "How many orders were placed each day this week?"

## 🔧 API Endpoints

### Connections

- `POST /api/connections/` - Create database connection
- `GET /api/connections/` - List all connections
- `DELETE /api/connections/{id}` - Remove connection
- `GET /api/connections/{id}/test` - Test connection

### Schema

- `GET /api/schema/{connection_id}` - Get database schema
- `GET /api/schema/{connection_id}/tables` - List tables
- `GET /api/schema/{connection_id}/tables/{table}` - Get table details

### Queries

- `GET /api/queries/ai/status` - Check AI service status and connectivity
- `POST /api/queries/` - Execute natural language query
- `GET /api/queries/history` - Get query history
- `POST /api/queries/{id}/rerun` - Rerun query
- `DELETE /api/queries/{id}` - Delete query from history

## 🔒 Security & Privacy Features

- **Read-only Database Access**: All connections are restricted to SELECT operations
- **SQL Injection Protection**: Query sanitization and validation
- **Connection Pooling**: Efficient database connection management
- **Error Handling**: Comprehensive error responses and logging
- **Local AI Option**: Process data completely offline with LM Studio
- **No Data Sharing**: Local processing ensures your data stays private

## 🎨 Color Scheme

- **Primary**: #9ACD32 (Yellow Green)
- **Secondary**: #7CB342 (Light Green)
- **Accent Colors**: #689F38, #558B2F, #33691E

## 🚧 Future Enhancements

- [ ] Export charts/reports to PDF or CSV
- [ ] Preset query templates for common analytics
- [ ] Session context for follow-up queries
- [ ] Advanced chart customization
- [ ] Multi-database query joins
- [ ] Scheduled query execution
- [ ] User authentication and permissions
- [ ] Dashboard sharing and collaboration

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

If you have any questions or issues, please open an issue on GitHub or contact the development team.

---

Built with ❤️ using Python FastAPI and React TypeScript
