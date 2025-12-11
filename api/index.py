import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set Vercel environment variable
os.environ['VERCEL'] = '1'

from app import app

# Vercel expects a handler function
def handler(request):
    return app(request.environ, request.start_response)

# Also export app directly for compatibility
__all__ = ['app', 'handler']
