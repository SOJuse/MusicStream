from app import app, db

with app.app_context():
    from app.models import User, FriendShips
    db.create_all()


if __name__ == "__main__":
    app.run()
