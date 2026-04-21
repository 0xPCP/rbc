import time
from app import create_app
from app.extensions import db
from sqlalchemy.exc import OperationalError

app = create_app()

# Wait for the database to be ready (relevant for Docker Compose cold starts)
with app.app_context():
    for attempt in range(15):
        try:
            db.create_all()
            break
        except OperationalError:
            if attempt == 14:
                raise
            time.sleep(2)

if __name__ == '__main__':
    app.run()
