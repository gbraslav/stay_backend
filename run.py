from app import create_app
from app.config import config
import os

print(config[os.environ.get('FLASK_ENV', 'development')])

app = create_app(config[os.environ.get('FLASK_ENV', 'development')])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)