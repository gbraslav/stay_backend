from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flasgger import Swagger
from app.config import Config
import logging

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    CORS(app)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set Flask app logger to debug level
    app.logger.setLevel(logging.INFO)



    # Initialize Swagger documentation
    from app.docs import swagger_template, swagger_config
    swagger = Swagger(app, template=swagger_template, config=swagger_config)
    
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    with app.app_context():
        db.create_all()

        # Restore user sessions from persistent storage
        try:
            from app.utils.startup import restore_user_sessions
            restore_user_sessions()
        except Exception as e:
            # Don't let startup session restoration fail the app
            print(f"Warning: Failed to restore user sessions: {e}")

    return app