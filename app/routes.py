import json
import datetime
import logging

from app import app, db, redis
from flask import render_template, request, jsonify
from .models import Task
from .config import IN_CHANNEL, OUT_CHANNEL


def task_handler():
    logging.debug("start task handler")
    channel = redis.pubsub()
    channel.subscribe(OUT_CHANNEL)
    for r in channel.listen():
        try:
            if r['type'] == 'message':
                result = json.loads(r['data'].decode("utf-8"))
                logging.debug("New incoming message: {}".format(result))

                task_id = result["id"]
            else:
                continue
        except KeyError:
            logging.debug("Bad data (id dont exist)")
            continue
        except UnicodeDecodeError:
            logging.debug("Error decode data")
            continue

        task = Task().query.get(task_id)
        if task is None:
            logging.debug("Task not found")
            continue

        if 'start' in result:
            task.start_time = datetime.datetime.fromtimestamp(result['start'])
        if 'exec' in result:
            task.exec_time = result['exec']
        if 'error' in result:
            task.exec_time = -1
        db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


def task_info(task_id):
    task = Task.query.get(task_id)
    if task is None:
        return jsonify({'error': 'task not found'}), 404

    result = {
        'status': 'In Queue',
        'create_time': task.create_time.timestamp(),
    }
    if task.start_time is not None:
        result['status'] = 'Run'
        result['start_time'] = task.start_time.timestamp() if task.start_time else 0
    if task.exec_time == -1:
        result['status'] = 'Error occurred'
    if task.exec_time > 0:
        result['status'] = 'Completed'
        result['time_to_execute'] = task.exec_time

    return jsonify(result), 200


@app.route('/task', methods=['GET'])
def task():
    if 'id' in request.values:
        return task_info(request.values['id'])

    # else create new task
    task = Task()
    db.session.add(task)
    db.session.commit()
    redis.publish(IN_CHANNEL, str(task.id))
    return jsonify({"id": task.id}), 201
