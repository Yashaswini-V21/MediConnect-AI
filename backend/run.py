"""Production-like local entrypoint for the backend.
Starts Flask-SocketIO in a mode compatible with the current environment.
"""

from app import app
from extensions import socketio


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
