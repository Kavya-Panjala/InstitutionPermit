import os
import logging
from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager


# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1) # needed for url_for to generate with https

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# Register custom template filters
from utils import timesince, get_status_badge_class
app.jinja_env.filters['timesince'] = timesince
app.jinja_env.filters['get_status_badge_class'] = get_status_badge_class

# Add context processor for global template variables
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Import and register blueprints
with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401
    from auth import auth_bp
    from events import events_bp
    from outpass import outpass_bp
    from dashboard import dashboard_bp
    from attendance import attendance_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(outpass_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp)
    
    # Create all database tables
    db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))
