import redis
import threading
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('app.config')
db = SQLAlchemy(app)
redis = redis.Redis(**app.config['REDIS_CONFIG'])

from app import routes

t = threading.Thread(target=routes.task_handler)
t.start()
