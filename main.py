from app import create_app, db
import os

app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug, port=port, host="0.0.0.0")
