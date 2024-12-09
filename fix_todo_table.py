from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Add sort_order column if it doesn't exist
    try:
        db.session.execute(text('ALTER TABLE todo ADD COLUMN sort_order INTEGER DEFAULT 0'))
        db.session.commit()
        print("Added sort_order column successfully")
    except Exception as e:
        print(f"Note: {str(e)}")
        db.session.rollback()

    # Try to copy data from order to sort_order if order exists
    try:
        db.session.execute(text('UPDATE todo SET sort_order = "order"'))
        db.session.commit()
        print("Copied data from order to sort_order")
    except Exception as e:
        print(f"Note: {str(e)}")
        db.session.rollback()

    # Try to drop order column if it exists
    try:
        db.session.execute(text('ALTER TABLE todo DROP COLUMN "order"'))
        db.session.commit()
        print("Dropped order column successfully")
    except Exception as e:
        print(f"Note: {str(e)}")
        db.session.rollback()

print("Table update complete")
