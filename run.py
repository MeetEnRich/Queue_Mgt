"""
FULafia Digital Queue Management System (DQMS)
===============================================
Entry point for the Flask application.
Loads environment variables and starts the development server on localhost:5000.
"""

from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
