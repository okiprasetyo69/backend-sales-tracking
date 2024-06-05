from flask_socketio import SocketIO

socketio = SocketIO(async_mode='threading', ping_timeout=300000, cors_allowed_origins="*")
