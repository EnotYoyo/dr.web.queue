import logging
import threading
import unittest
import timeout_decorator
import multiprocessing

import time
from typing import List

from app import dispatcher


class TestQueue(unittest.TestCase):

    def test_size(self):
        def queue_get_size(queue: dispatcher.Queue, count: int):
            for _ in range(count):
                queue.size()

        queue = dispatcher.Queue()
        queue.add({"a": "b"})
        queue.add([i for i in range(10)])
        queue.add("test_string")

        threads = []
        for i in range(2):
            t = threading.Thread(target=queue_get_size, args=(queue, 1000))
            t.start()
            threads.append(t)

        self.assertEqual(queue.size(), 3)
        for t in threads:
            t.join(2)

    def test_shared_write(self):
        def queue_get_size(queue: dispatcher.Queue, count: int):
            for i in range(count):
                queue.add(i)

        queue = dispatcher.Queue()
        threads = []
        thread_number = 2
        elements_count = 100
        for i in range(thread_number):
            t = threading.Thread(target=queue_get_size, args=(queue, elements_count))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(2)
        self.assertEqual(queue.size(), thread_number * elements_count)


class TestWorker(unittest.TestCase):
    def _processes_is_alive(self, processes: List[multiprocessing.Process]):
        for process in processes:
            self.assertTrue(process.is_alive())

    def test_poison_pill(self):
        def target():
            time.sleep(1)

        tasks_queue = dispatcher.Queue()
        result_queue = dispatcher.Queue()

        processes = []
        for _ in range(2):
            process = multiprocessing.Process(target=dispatcher.worker, args=(target, tasks_queue, result_queue))
            process.start()
            processes.append(process)

        for i in range(len(processes)):
            tasks_queue.add(dispatcher.POISON_PILL)

        while tasks_queue.size() > 0:
            pass

        time.sleep(2)  # need time for terminate
        for process in processes:
            self.assertFalse(process.is_alive())

    def test_bad_data(self):
        def target():
            time.sleep(1)

        tasks_queue = dispatcher.Queue()
        result_queue = dispatcher.Queue()

        processes = []
        for _ in range(2):
            process = multiprocessing.Process(target=dispatcher.worker, args=(target, tasks_queue, result_queue))
            process.start()
            processes.append(process)

        for i in range(10):
            tasks_queue.add(None)
        self._processes_is_alive(processes)

        for i in range(10):
            tasks_queue.add("aaa")
        self._processes_is_alive(processes)

        for i in range(10):
            tasks_queue.add(37331)
        self._processes_is_alive(processes)

        for i in range(10):
            tasks_queue.add({})
        self._processes_is_alive(processes)

        for i in range(len(processes)):
            tasks_queue.add(dispatcher.POISON_PILL)

    def test_good_data(self):
        def target():
            time.sleep(1)

        tasks_queue = dispatcher.Queue()
        result_queue = dispatcher.Queue()

        processes = []
        for _ in range(2):
            process = multiprocessing.Process(target=dispatcher.worker, args=(target, tasks_queue, result_queue))
            process.start()
            processes.append(process)

        tasks_count = 2
        tasks_results = 2 * tasks_count
        for i in range(tasks_count):
            tasks_queue.add({'id': 123})

        while tasks_results > 0:
            r = result_queue.get(timeout=3)
            self.assertIsNotNone(r)
            tasks_results -= 1

        for process in processes:
            process.terminate()


class TestDispatcher(unittest.TestCase):
    # TODO: need more test for dispatcher
    def test_create_dispatcher(self):
        d = dispatcher.Dispatcher(sum, 'test1', 'test2', 10)
        self.assertEqual(len(d.processes), 10)
        del d


# TODO: need tests for routers
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    timeout_decorator.timeout(10, use_signals=False)(unittest.main)()
