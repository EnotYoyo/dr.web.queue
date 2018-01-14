import datetime
from app import db


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)
    create_time = db.Column(db.TIMESTAMP, default=datetime.datetime.utcnow)
    start_time = db.Column(db.TIMESTAMP)
    exec_time = db.Column(db.FLOAT, default=0)

    def __repr__(self):
        return '<Task({id})>'.format(id=self.id)
