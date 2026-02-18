from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import sys
# Ensure inner package imports work when running from repository root
sys.path.insert(0, "personal-analytics-dashboard")
from database import Base
from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Determine DB name
db_name = DB_NAME or "analytics_db"

# Create an engine that connects to the server (no specific database)
server_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/"
engine_server = create_engine(server_url)

try:
    with engine_server.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        conn.commit()
    print(f"Database '{db_name}' ensured.")
except SQLAlchemyError as e:
    print("Error creating database:", e)
    raise

# Now create an engine that points to the created database and create tables
db_url_with_name = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
engine = create_engine(db_url_with_name)

try:
    # Import models so they're registered on Base.metadata
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("Tables created (if not existing).")
except SQLAlchemyError as e:
    print("Error creating tables:", e)
    raise
