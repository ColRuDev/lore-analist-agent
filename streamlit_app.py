"""
Streamlit entry point.

Run from the project root:
    streamlit run streamlit_app.py
"""

from dotenv import load_dotenv

load_dotenv()

from src.streamlit.app import run

run()
