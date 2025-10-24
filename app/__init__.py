from flask import Flask
from app.config import Config
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Register blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.trends import trends_bp
    from app.routes.powerlist import powerlist_bp
    from app.routes.validation import validation_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(trends_bp)
    app.register_blueprint(powerlist_bp)
    app.register_blueprint(validation_bp)
    app.register_blueprint(admin_bp)
    
    return app

# Create the app instance that Vercel will look for
app = create_app()