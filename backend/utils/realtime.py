"""
Simple in-memory pub/sub for Server-Sent Events (SSE).
Not suitable for multi-process production; good for local/dev and demo.
"""
import queue
import threading

# List of subscriber queues
SUBSCRIBERS = []
LOCK = threading.Lock()


def subscribe():
    """Create a new queue for a subscriber and return it."""
    q = queue.Queue()
    with LOCK:
        SUBSCRIBERS.append(q)
    return q


def unsubscribe(q):
    with LOCK:
        try:
            SUBSCRIBERS.remove(q)
        except ValueError:
            pass


def publish_event(event: dict):
    """Publish an event dict to all subscribers."""
    with LOCK:
        for q in list(SUBSCRIBERS):
            try:
                q.put(event)
            except Exception:
                # ignore subscriber failures
                pass
