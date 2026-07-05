"""
Root application file for deployment.
Re-exports the FastAPI app from the backend module.
"""
import sys
import os

# Add backend to path so relative imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and re-export the app
from backend.main import app

__all__ = ['app']
