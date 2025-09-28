# AskDash Backend

## Setup

1. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` file with your configuration:

```
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=your_database_url_here
SECRET_KEY=your_secret_key_here
```

4. Run the server:

```bash
uvicorn main:app --reload
```

## API Documentation

Once running, visit:

- API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## How to Run the Backend

1. **Activate your Python virtual environment:**

   ```
   source venv/bin/activate
   ```

2. **Start the FastAPI backend (from the `backend` directory):**
   ```
   cd backend
   uvicorn main:app --reload --port 8001
   ```

- The backend will be available at [http://127.0.0.1:8001](http://127.0.0.1:8001).
- Change the port (`--port 8001`) if needed.

---
