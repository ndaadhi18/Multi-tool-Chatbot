# Multi-Tool Conversational AI Assistant

This project is a conversational assistant built using LangGraph, Gemini models, and Streamlit. It supports multiple tools such as weather lookup, stock price retrieval, basic math calculation, time zone conversion, currency conversion, random facts, and jokes. The assistant maintains conversation history using a SQLite checkpointer and allows switching between multiple conversation threads.

## Features
- Stateful conversational memory using SQLite.
- Tool execution based on user intent.
- Web search, weather, stock price, jokes, calculator, time zone, and currency conversion tools.
- Streamlit interface with conversation list and delete functionality.
- Streaming response interface for natural interaction.

## Technology Stack
- Python
- LangGraph
- LangChain (Google Generative AI)
- Streamlit
- SQLite
- Requests (API calls)

## File Structure
project/
│ frontend.py # Streamlit interface
│ backend.py # Chat logic and tool definitions
│ requirements.txt # Dependencies


## Setup Instructions
1. Install dependencies:
```terminal/bash
pip install -r requirements.txt
```

2. Create `.streamlit/secrets.toml`:
```
GOOGLE_API_KEY = "<your_google_api_key>"
```


3. Run the application:
```
streamlit run frontend.py
```
