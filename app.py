from flask import Flask
from flask_login import LoginManager
from models import User, init_db
from config import Config
from routes import main_routes, auth_routes, admin_routes, courier_routes
from utils import update_order_statuses
import threading

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth_routes.login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

app.register_blueprint(main_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(admin_routes)
app.register_blueprint(courier_routes)

init_db()

status_update_thread = threading.Thread(target=update_order_statuses, daemon=True)
status_update_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
