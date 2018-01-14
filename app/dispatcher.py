import time
import json
from typing import Any
import redis
import logging
import multiprocessing

POISON_PILL = 'POISON_PILL'


class Queue(object):
    """
    Simple objects queue
    using multiprocessing condition and shared multiprocessing list
    """

    def __init__(self):
        self.lock = multiprocessing.Condition()
        self.queue = multiprocessing.Manager().list()

    def size(self):
        with self.lock:
            return len(self.queue)

    def get(self, block: bool = True, timeout=None) -> Any:
        with self.lock:
            if block:
                # this safe check because self.add notify only one
                self.lock.wait_for(lambda: len(self.queue) != 0, timeout)
            try:
                element = self.queue.pop()
            except IndexError:
                element = None
            return element

    def add(self, info: Any):
        with self.lock:
            self.queue.insert(0, info)
            self.lock.notify()


def worker(target_function, tasks_queue: Queue, result_queue: Queue):
    while True:
        task = tasks_queue.get()
        if isinstance(task, str) and task == POISON_PILL:
            break
        if task is None or not isinstance(task, dict) or 'id' not in task:
            continue
        start_time = time.time()
        result_queue.add({'id': task['id'], 'start': start_time})
        try:
            target_function()
        except Exception as e:
            result_queue.add({'id': task['id'], 'error': str(e)})
        else:
            result_queue.add({'id': task['id'], 'exec': time.time() - start_time})


class Dispatcher(object):
    def __init__(self, target_function, in_channel: str, out_channel: str, max_workers=2, redis_host='localhost',
                 redis_port=6379, redis_db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.incoming = self.redis.pubsub()
        self.incoming.subscribe(in_channel)
        self.out_channel = out_channel

        self.tasks_queue = Queue()
        self.result_queue = Queue()
        self.max_tasks = max_workers
        self.target_function = target_function

        self.processes = []
        for _ in range(self.max_tasks):
            self.processes.append(self.create_process())

    def create_process(self) -> multiprocessing.Process:
        process = multiprocessing.Process(target=worker, args=(self.target_function, self.tasks_queue, self.result_queue))
        process.start()
        return process

    def add_new_task(self, task_id: int):
        logging.debug("Create new task (id: {})".format(task_id))
        self.tasks_queue.add({
            "id": task_id
        })

    def check_processes_state(self):
        for process in self.processes:
            if not process.is_alive():
                logging.debug("Process {} is died".format(process.name))
                del process
                self.processes.append(self.create_process())

    def check_new_tasks(self):
        response = self.incoming.parse_response(block=False)
        if response is not None:
            response = self.incoming.handle_message(response)
            if response['type'] == 'message':
                logging.debug("New incoming message: {}".format(response['data']))
                try:
                    task_id = int(response['data'].decode("utf-8"))
                    self.add_new_task(task_id)
                except UnicodeDecodeError:
                    logging.debug("Bad incoming message")

    def check_running_task_state(self):
        task = self.result_queue.get(block=False)
        if task is not None:
            logging.debug("Publish info about task (id: {}): {}".format(task["id"], task))
            self.redis.publish(self.out_channel, json.dumps(task))

    def run(self):
        logging.debug("Start dispatcher")
        while True:
            self.check_new_tasks()
            self.check_running_task_state()
            self.check_processes_state()

    def __del__(self):
        for process in self.processes:
            if process.is_alive():
                process.terminate()


def main():
    import argparse
    from test import main as test_func

    parser = argparse.ArgumentParser(description='Simple task queue.')
    parser.add_argument('in_channel', metavar='in_channel', type=str,
                        help='channel for incoming tasks')
    parser.add_argument('out_channel', metavar='out_channel', type=str,
                        help='channel for tasks result')
    parser.add_argument('--workers', dest='workers', type=int, default=2,
                        help='number workers')
    parser.add_argument('--host', dest='host', type=str, default='localhost',
                        help='redis host')
    parser.add_argument('--port', dest='port', type=int, default=6379,
                        help='redis port')
    parser.add_argument('--db', dest='db', type=int, default=0,
                        help='redis database')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show debug info")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    dispatcher = Dispatcher(
        target_function=test_func,
        in_channel=args.in_channel,
        out_channel=args.out_channel,
        max_workers=args.workers,
        redis_host=args.host,
        redis_port=args.port,
        redis_db=args.db
    )
    dispatcher.run()


if __name__ == '__main__':
    main()
