# nexus-ai

A local-first, CLI-based productivity and planning assistant. See the `nexus-ai-Docs` folder for detailed documentation.

## Project Structure

```
├── src/
│   ├── core/
│   │   └── database.py
│   ├── cli/
│   └── integrations/
├── scripts/
│   └── initialize_database.py
├── data/
├── requirements.txt
├── .env.example
├── README.md
```

## Getting Started

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```bash
   python scripts/initialize_database.py
   ```
4. Check that `data/nexus.db` exists and contains the required tables.