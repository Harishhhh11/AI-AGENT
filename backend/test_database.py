from sqlalchemy import text

from app.database.session import SessionLocal


db = SessionLocal()

try:

    result = db.execute(
        text("SELECT current_database(), current_user")
    )

    database, user = result.fetchone()

    print("Database:", database)
    print("User:", user)
    print("Database connection successful.")

finally:

    db.close()