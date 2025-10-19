from flask import Flask
from flask_cors import CORS
from api.routes import api_blueprint

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)