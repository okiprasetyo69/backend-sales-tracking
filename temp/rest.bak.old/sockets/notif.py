# from rest.http import socketio
from rest.helpers import socketio, USERS_NOTIF
from flask_socketio import emit

import json
import time

# USERS_NOTIF = []

@socketio.on('connect-notif')
def connection_notif_socket(socket_data):
    """
    :event: 'connection'
    :return:
    init connection
    """
    user_id = socket_data['user_id']
    if len(USERS_NOTIF) == 0:
        message = {
            "user_id": user_id,
            "total": 0
        }
    else:
        message = {
            "user_id": user_id,
            "total": 0
        }
        for rec in USERS_NOTIF:
            if rec['user_id'] == user_id:
                message = {
                    "user_id": rec['user_id'],
                    "total": rec['total']
                }

    emit('notif-{}'.format(user_id), [message], broadcast=True)


@socketio.on('userid-set')
def userid_set(socket_data):
    """
    :event: 'user-set'
    :param socket_data:
    {
        "user_id": (user_id),
        "name": (name),
        "job_function": (job_function),
        "branch_id": (branch_id),
        "lat": (lat),
        "lng": (lng)
    }
    :return:
    """
    # socket_data_json = json.loads(socket_data)

    user_id = socket_data['user_id']
    total = 0
    # if user_controller.check_user_by_id(user_id):
    if len(USERS_NOTIF) == 0:
        USERS_NOTIF.append({
            "user_id": user_id,
            "total": total
        })
        message = {
            "user_id": user_id,
            "total": total
        }
    else:
        not_duplicate = True
        for rec in USERS_NOTIF:
            if rec['user_id'] == user_id:
                not_duplicate = False
                message = {
                    "user_id": rec['user_id'],
                    "total": rec['total']
                }
        if not_duplicate:
            USERS_NOTIF.append({
                "user_id": user_id,
                "total": total
            })

            message = {
                "user_id": user_id,
                "total": total
            }
    emit('notif-{}'.format(user_id), [message], broadcast=True)


@socketio.on('userid-reset')
def user_unset(socket_data):
    """
    :event: 'user-unset'
    :param socket_data:
    {
        "user_id": (user_id)
    }
    :return:
    """

    user_id = socket_data['user_id']
    message = {
        "user_id": user_id,
        "total": 0
    }

    for rec in USERS_NOTIF:
        if rec['user_id'] == int(user_id):
            rec['total'] = 0
            message = {
                "user_id": rec['user_id'],
                "total": 0
            }

    emit('notif-{}'.format(user_id), [message], broadcast=True)


@socketio.on('add-notif')
def add_notif_inc(socket_data):
    # socket_data_json = json.loads(socket_data)
    print('================== DEBUG =================')
    print(socket_data)
    user_id = socket_data['user_id']
    message = None
    # if user_controller.check_user_by_id(user_id):
    for rec in USERS_NOTIF:
        if rec['user_id'] == user_id:
            rec['total'] += 1
            message = rec

    if message:
        pass
    else:
        USERS_NOTIF.append({
            "user_id": user_id,
            "total": 1
        })
        message = {
            "user_id": user_id,
            "total": 1
        }

    emit('notif-{}'.format(user_id), [message], broadcast=True)
