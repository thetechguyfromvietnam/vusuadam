import sys
import os

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Set Vercel environment variable
os.environ['VERCEL'] = '1'

# Import app after path is set
try:
    from app import app
    
    # Initialize database on first request (lazy initialization)
    @app.before_first_request
    def create_tables():
        try:
            from app import db
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")
    
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    raise

# Vercel Python runtime expects the app directly
# The @vercel/python builder wraps Flask apps automatically
handler = app
