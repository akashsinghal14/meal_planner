# Meal Planner AI Chat 🍽️

A Streamlit-based chat application that uses OpenAI's GPT models to provide meal planning, cooking advice, and recipe suggestions.

## Features ✨

- 💬 Interactive chat interface with OpenAI GPT
- 🍳 Specialized meal planning and cooking assistance
- 📱 Clean, responsive web interface
- 💾 Chat history management
- 🔧 Easy setup and configuration

## Prerequisites 📋

- Python 3.8 or higher
- OpenAI API key
- Virtual environment (recommended)

## Quick Start 🚀

### Option 1: Automatic Setup (Recommended)

1. **Activate your virtual environment:**
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. **Run the setup script:**
   ```bash
   python run_app.py
   ```
   
   This will automatically:
   - Check your .env file
   - Install all dependencies
   - Start the Streamlit application

### Option 2: Manual Setup

1. **Activate your virtual environment:**
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Configuration ⚙️

Make sure your `.env` file contains your OpenAI API key:

```
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage 💡

1. Open your browser and go to `http://localhost:8501`
2. Start chatting with the AI about:
   - Recipe suggestions
   - Meal planning advice
   - Nutritional information
   - Cooking tips and techniques
   - Ingredient substitutions

## Project Structure 📁

```
meal_planner/
├── app.py              # Main Streamlit application
├── run_app.py          # Setup and run helper script
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (API keys)
├── README.md          # This file
└── venv/             # Virtual environment
```

## Dependencies 📦

- `streamlit` - Web app framework
- `openai` - OpenAI API client
- `python-dotenv` - Environment variable management
- `pandas` - Data manipulation (for future features)

## Troubleshooting 🔧

### Common Issues

1. **"OpenAI API key not found" error:**
   - Make sure your `.env` file exists and contains `OPENAI_API_KEY=your_key`
   - Ensure the virtual environment is activated

2. **Module not found errors:**
   - Run `pip install -r requirements.txt`
   - Make sure you're in the activated virtual environment

3. **Port already in use:**
   - The app runs on port 8501 by default
   - You can specify a different port: `streamlit run app.py --server.port 8502`

## License 📄

This project is open source and available under the [MIT License](LICENSE).

## Contributing 🤝

Feel free to submit issues, feature requests, or pull requests to improve this meal planner application!
