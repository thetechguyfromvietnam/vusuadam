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
    
    # CRITICAL: Initialize database BEFORE any requests
    # This must happen at import time for Vercel
    try:
        with app.app_context():
            # Force create all tables
            db.create_all()
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Database initialized. Tables: {tables}")
            if 'cayxanh' not in tables:
                print("WARNING: cayxanh table not found after create_all()")
                # Try to create again
                db.create_all()
    except Exception as db_error:
        # Log error but continue - might be permission issue
        error_msg = f"Database initialization error: {str(db_error)}"
        print(error_msg)
        traceback.print_exc()
        # Don't raise - let the app start and handle errors in routes
    
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
