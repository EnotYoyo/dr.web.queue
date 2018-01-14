# config for Flask app

# config for postgres and sqlalchemy
POSTGRES = {
    'user': 'postgres',
    'password': 'postgres',
    'db': 'test_queue',
    'host': 'localhost',
    'port': '5432',
}
SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{password}@{host}:{port}/{db}'.format(**POSTGRES)

# redis config (constructor parameters)
# in code used: redis.Redis(**REDIS_CONFIG)
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

# channels for communicate Dispatcher and Flask app
IN_CHANNEL = 'task_queue'
OUT_CHANNEL = 'result_queue'
