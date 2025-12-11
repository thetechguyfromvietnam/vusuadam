import sys
import os
import traceback

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set Vercel environment variable
os.environ['VERCEL'] = '1'

# Import app after path is set
try:
    from app import app, db
    
    # Initialize database on first import (for Vercel)
    # Use try-except to handle any database errors gracefully
    try:
        with app.app_context():
            # Only create tables if they don't exist
            db.create_all()
    except Exception as db_error:
        # Log error but don't fail - database might already exist or have issues
        print(f"Database initialization warning: {str(db_error)}")
        # Don't print full traceback for database errors to avoid noise
    
except ImportError as import_error:
    # Critical error - cannot import app
    error_msg = f"CRITICAL: Cannot import app: {str(import_error)}"
    print(error_msg)
    traceback.print_exc()
    raise
except Exception as e:
    # Any other error
    error_msg = f"Unexpected error: {str(e)}"
    print(error_msg)
    traceback.print_exc()
    raise

# Vercel Python runtime expects the app directly
# The @vercel/python builder wraps Flask apps automatically
handler = app
