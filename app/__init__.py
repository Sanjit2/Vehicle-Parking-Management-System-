import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv

# Global db instance
_db = SQLAlchemy()

def _build_db_uri() -> str:
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "parking_system")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"


def create_app() -> Flask:
    # Load .env if present
    load_dotenv()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = _build_db_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    _db.init_app(app)

    # Ensure DB triggers/procs/functions are present. This will execute PROJECT/init_db.sql
    try:
        from .db_init import run_init_sql

        with app.app_context():
            run_init_sql(app)
    except Exception as e:
        # Log but do not stop app creation; initialization errors can be investigated separately
        app.logger.exception("Failed to run DB init SQL: %s", e)

    # Register blueprints
    from .routes import main_bp, api_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app

# convenient import alias
db = _db

