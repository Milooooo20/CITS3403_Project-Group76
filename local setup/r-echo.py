from app import create_app, db
from app.config import DeploymentConfig

if __name__ == '__main__':
    app = create_app(DeploymentConfig)
    app.run(debug=True, use_debugger=False, use_reloader=False)