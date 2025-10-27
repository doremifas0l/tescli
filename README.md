
# Personal Finance App

This is a personal finance application that uses Gemini AI to process transactions from natural language and categorize them automatically.

## Features

- Chat-based interface for adding transactions.
- AI-powered transaction parsing and categorization.
- SQLite database for storing transactions.
- GUI built with PyQt.

## Technologies Used

- Python
- PyQt6
- Google Gemini AI
- SQLite
- Pandas

## Getting Started

### Prerequisites

- Python 3.x
- Pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/doremifas0l/tescli.git
   cd tescli
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API Key:**
   - Get your Google AI API key from [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).
   - Open the `main.py` file and replace `"YOUR_API_KEY"` with your actual API key.

5. **Run the application:**
   ```bash
   python main.py
   ```

## Project Structure

```
.
├── .git
├── .gitignore
├── README.md
├── ai.py
├── database.py
├── finance.db
├── main.py
└── requirements.txt
```

- `main.py`: The main entry point of the application. It contains the PyQt GUI code and ties everything together.
- `ai.py`: Handles all the interactions with the Gemini AI API.
- `database.py`: Manages the SQLite database, including creating tables and performing CRUD operations.
- `requirements.txt`: A list of all the Python libraries required for the project.
- `finance.db`: The SQLite database file where all the transaction data is stored.
- `README.md`: This file, providing information about the project.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request. See `GUIDELINES.md` for more details.
