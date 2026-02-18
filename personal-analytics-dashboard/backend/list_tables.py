import sys
from sqlalchemy import create_engine, inspect

# Make the inner package importable when running from repository root
sys.path.insert(0, "personal-analytics-dashboard")
from backend.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

try:
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print('Using URL:', url)
    engine = create_engine(url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print('Tables:', tables)
except Exception as e:
    print('Error listing tables:', e)
    sys.exit(1)
