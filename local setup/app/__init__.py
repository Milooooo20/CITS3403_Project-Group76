from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import Config

# Initialize extensions
db = SQLAlchemy()
login = LoginManager()

# Set login view (used by @login_required redirects)
login.login_view = 'main.sign_in'  # Route name, not template name
login.login_message_category = 'info'

def create_app(config):
    app = Flask(__name__)

    # Configuration
    app.config.from_object(config)


    from app.blueprints import blueprint
    app.register_blueprint(blueprint)


    # Initialize extensions with the app
    db.init_app(app)
    login.init_app(app)

    
    # Import and register routes
    #from app.routes import register_routes  # Import the function that registers routes
    #register_routes(app)  # Call the function to register the routes

    return app