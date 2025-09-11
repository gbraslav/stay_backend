from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flasgger import Swagger
from app.config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    CORS(app)
    
    # Initialize Swagger documentation
    from app.docs import swagger_template, swagger_config
    swagger = Swagger(app, template=swagger_template, config=swagger_config)
    
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    with app.app_context():
        db.create_all()
    
    return app