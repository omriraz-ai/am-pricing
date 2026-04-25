from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE projects ADD COLUMN business_status TEXT NOT NULL DEFAULT 'בטיפול'"))
    conn.execute(text("ALTER TABLE projects ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT 0"))
    conn.commit()

print("Migration הושלמה")