from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login = LoginManager()
csrf = CSRFProtect()

# Set login view (used by @login_required redirects)
login.login_view = 'sign_in'  # Route name, not template name
login.login_message_category = 'info'

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = 'secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with the app
    db.init_app(app)
    login.init_app(app)
    csrf.init_app(app)

    # Import and register routes
    from app.routes import register_routes  # Import the function that registers routes
    register_routes(app)  # Call the function to register the routes

    return app
