import os
import logging.config

from datetime import timedelta
from flask import Flask
from flask_jwt import JWT
from flask_cors import CORS
from flask_compress import Compress
from logging.handlers import RotatingFileHandler
# from flask_socketio import SocketIO

from rest.helpers import mysql, fcm, socketio, mail
from rest.models import UserModel
from rest import routes

User = UserModel()
compress = Compress()
cors = CORS()
# socketio = SocketIO(async_mode='threading', ping_timeout=300000)

_jwt = JWT(authentication_handler=User.authenticate, identity_handler=User.identity)


def create_app(configuration):
    app = Flask(__name__.split(',')[0], static_url_path='/static', static_folder='../static')

    app.register_blueprint(routes.auth.bp)
    app.register_blueprint(routes.error.bp)
    app.register_blueprint(routes.menu.bp)
    app.register_blueprint(routes.user.bp)
    app.register_blueprint(routes.employee.bp)
    app.register_blueprint(routes.setting.bp)
    app.register_blueprint(routes.branches.bp)
    app.register_blueprint(routes.division.bp)
    app.register_blueprint(routes.asset.bp)
    app.register_blueprint(routes.area.bp)
    app.register_blueprint(routes.sales.bp)
    app.register_blueprint(routes.visit.bp)
    app.register_blueprint(routes.customer.bp)
    app.register_blueprint(routes.permissions.bp)
    app.register_blueprint(routes.inbox.bp)
    app.register_blueprint(routes.activity.bp)
    app.register_blueprint(routes.logistic.bp)
    app.register_blueprint(routes.delivery.bp)
    app.register_blueprint(routes.statistic.bp)
    app.register_blueprint(routes.approval.bp)
    app.register_blueprint(routes.visiteye.bp)
    app.register_blueprint(routes.wso.bp)

    # TODO: Load Configuration
    app.config.from_object(configuration)

    logging.config.dictConfig(configuration.LOG_CONFIGURATION)
    handler = RotatingFileHandler(
        configuration.LOG_FILE, maxBytes=configuration.LOG_MAX_BYTES, backupCount=configuration.LOG_ROTATE_COUNT
    )
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    mysql.init_app(app)
    mail.init_app(app)
    fcm.init_app(app)

    _jwt.init_app(app)
    compress.init_app(app)
    cors.init_app(app=app, resources={r"/*": {"origins": "*"}})
    socketio.init_app(app)
    from rest.sockets import livemap
    from rest.sockets import notif

    return app
