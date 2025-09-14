# utils/state_manager.py
import threading

class ThreadSafeStore:
    def __init__(self):
        self.responses = {}
        self.requests_threads = {}
        self.lock = threading.Lock()

    def get_response(self, request_id):
        with self.lock:
            return self.responses.get(request_id)

    def set_response(self, request_id, response):
        with self.lock:
            self.responses[request_id] = response

    def set_thread(self, request_id, thread):
        with self.lock:
            self.requests_threads[request_id] = thread

    def remove_thread(self, request_id):
        with self.lock:
            self.requests_threads.pop(request_id, None)

    def is_in_progress(self, request_id):
        with self.lock:
            return request_id in self.requests_threads
