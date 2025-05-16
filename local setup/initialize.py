from app import create_app, db
from app.config import DeploymentConfig

app = create_app(DeploymentConfig)

with app.app_context():
    db.create_all()
