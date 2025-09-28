# Using LM Studio with AskDash

AskDash now supports local AI models through LM Studio! This guide will help you set up and use local AI models for natural language to SQL conversion.

## What is LM Studio?

LM Studio is a desktop application that allows you to run Large Language Models (LLMs) locally on your machine. It provides an OpenAI-compatible API endpoint, making it easy to integrate with applications like AskDash.

## Prerequisites

1. **LM Studio**: Download and install from [https://lmstudio.ai/](https://lmstudio.ai/)
2. **Compatible Model**: Download a code-capable model (see recommended models below)
3. **AskDash**: This modified version of AskDash with LM Studio support

## Recommended Models

For SQL generation, we recommend models that are good at code and reasoning:

### Small Models (4-8GB RAM)
- **Code Llama 7B Instruct** - Excellent for code generation
- **Mistral 7B Instruct** - Good balance of size and performance
- **Zephyr 7B Beta** - Strong instruction following

### Medium Models (16-32GB RAM)
- **Code Llama 13B Instruct** - Better accuracy for complex queries
- **Mistral 8x7B Instruct** (Mixtral) - Very capable model
- **Llama 2 13B Chat** - Good general performance

### Large Models (32GB+ RAM)
- **Code Llama 34B Instruct** - Best accuracy for complex SQL
- **Llama 2 70B Chat** - Excellent performance but requires significant RAM

## Step-by-Step Setup

### 1. Install and Configure LM Studio

1. Download and install LM Studio from the official website
2. Launch LM Studio
3. Go to the "Discover" tab and search for a model (e.g., "Code Llama 7B Instruct")
4. Download your chosen model (this may take some time depending on the model size)

### 2. Load and Start the Model

1. Go to the "Chat" tab in LM Studio
2. Select your downloaded model from the dropdown
3. Click "Start Server" to begin serving the model
4. Note the server URL (usually `http://localhost:1234`)
5. The model is now ready to receive API requests!

### 3. Configure AskDash

1. Copy the environment example file:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Edit the `.env` file with your LM Studio settings:
   ```bash
   # AI Configuration - Use LM Studio
   AI_PROVIDER=lmstudio
   
   # LM Studio Configuration
   LM_STUDIO_BASE_URL=http://localhost:1234/v1
   LM_STUDIO_MODEL=local-model  # This is usually "local-model" in LM Studio
   
   # AI Model Parameters (adjust based on your model's capabilities)
   AI_TEMPERATURE=0.1
   AI_MAX_TOKENS=1000
   
   # Other settings...
   SECRET_KEY=your-secret-key-change-this-in-production
   DATABASE_URL=sqlite:///./test.db
   ```

### 4. Start AskDash

1. Start the backend:
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. Visit `http://localhost:3000` to use AskDash with your local AI model!

## Testing the Setup

### Check AI Status

You can test if everything is working by calling the AI status endpoint:

```bash
curl http://localhost:8000/api/queries/ai/status
```

Expected response:
```json
{
  "status": "success",
  "provider": "lmstudio",
  "model": "local-model",
  "base_url": "http://localhost:1234/v1",
  "response": "Hello",
  "message": "Successfully connected to lmstudio"
}
```

### Test SQL Generation

Try asking AskDash a natural language question about your database. If everything is set up correctly, your local model will generate SQL queries!

## Troubleshooting

### Common Issues

#### 1. Connection Error
**Error**: "Cannot connect to lmstudio at http://localhost:1234/v1"

**Solutions**:
- Make sure LM Studio is running and the server is started
- Check that the port (1234) matches your LM Studio server port
- Verify the `LM_STUDIO_BASE_URL` in your `.env` file

#### 2. Model Not Found
**Error**: "Model 'local-model' not found"

**Solutions**:
- Ensure you have a model loaded in LM Studio
- Check that you've clicked "Start Server" in LM Studio
- The model name in `.env` should usually be `local-model`

#### 3. Slow Responses
**Issue**: Queries take a long time to complete

**Solutions**:
- Use a smaller model if you have limited RAM
- Increase `AI_MAX_TOKENS` if responses are being cut off
- Adjust `AI_TEMPERATURE` (lower = more consistent, higher = more creative)

#### 4. Poor SQL Quality
**Issue**: Generated SQL is incorrect or low quality

**Solutions**:
- Try a larger, more capable model
- Use models specifically trained for code (like Code Llama)
- Ensure your database schema is well-documented
- Lower the temperature for more consistent results

## Alternative Configurations

### Using Other OpenAI-Compatible APIs

If you're using a different local inference server (like Ollama, text-generation-webui, etc.), you can use the `openai-compatible` provider:

```bash
# AI Configuration
AI_PROVIDER=openai-compatible

# Your API Configuration
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=your-api-key-if-required

# Model name (check your server's documentation)
AI_MODEL=your-model-name
```

### Fallback to OpenAI

You can always switch back to OpenAI by changing your `.env` file:

```bash
# AI Configuration
AI_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
```

## Performance Tips

1. **Model Selection**: Choose a model appropriate for your hardware
2. **Context Length**: Some models support longer contexts, useful for complex schemas
3. **Quantization**: Use quantized models (Q4, Q5) to reduce memory usage
4. **Batch Processing**: LM Studio can handle multiple requests efficiently
5. **Temperature Settings**: Lower values (0.1-0.3) work better for SQL generation

## Security Considerations

1. **Local Processing**: All data stays on your machine - no external API calls
2. **Network Access**: LM Studio only listens on localhost by default
3. **Data Privacy**: Your database schemas and queries are not sent to external services
4. **Model Security**: Only download models from trusted sources

## Benefits of Using Local Models

- **Privacy**: All processing happens locally
- **Cost**: No API usage fees after initial setup
- **Speed**: No network latency (once loaded)
- **Customization**: Use specialized models for your domain
- **Offline**: Works without internet connection
- **Control**: Full control over model behavior and updates

## Support

If you encounter issues:

1. Check LM Studio's logs and console output
2. Verify your model is compatible with instruction following
3. Test the LM Studio API directly with curl
4. Check the AskDash backend logs for detailed error messages

For LM Studio-specific issues, visit their documentation at [https://lmstudio.ai/docs](https://lmstudio.ai/docs)