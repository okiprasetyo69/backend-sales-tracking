# from rest.http import socketio
from rest.helpers import socketio
from flask_socketio import emit

import json
import time

USERS = []


@socketio.on('connect')
def connection_socket():
    """
    :event: 'connection'
    :return:
    init connection
    """
    emit('markers', USERS, broadcast=True)


@socketio.on('user-set')
def user_set(socket_data):
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
    name = socket_data['name']
    job_function = socket_data['job_function']
    branch_id = socket_data['branch_id']
    division_id = socket_data['division_id']
    lat = socket_data['lat']
    lng = socket_data['lng']
    asset_code = socket_data['asset_code']
    asset_name = socket_data['asset_name']
    # if user_controller.check_user_by_id(user_id):
    if len(USERS) == 0:
        USERS.append({
            "user_id": user_id,
            "name": name,
            "job_function": job_function,
            "branch_id": branch_id,
            "division_id": division_id,
            "lat": lat,
            "lng": lng,
            "asset_code": asset_code,
            "asset_name": asset_name
        })
    else:
        not_duplicate = True
        for rec in USERS:
            if rec['user_id'] == user_id:
                not_duplicate = False
        if not_duplicate:
            USERS.append({
                "user_id": user_id,
                "name": name,
                "job_function": job_function,
                "branch_id": branch_id,
                "division_id": division_id,
                "lat": lat,
                "lng": lng,
                "asset_code": asset_code,
                "asset_name": asset_name
            })
    emit('markers', USERS, broadcast=True)


@socketio.on('user-unset')
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
    index_delete = None
    idx = 0
    if len(USERS) != 0:
        for rec in USERS:
            if rec['user_id'] == user_id:
                index_delete = idx
            idx += 1
    if index_delete is not None:
        del USERS[index_delete]

    emit('markers', USERS, broadcast=True)


@socketio.on('change-location')
def change_location(socket_data):
    # socket_data_json = json.loads(socket_data)
    print('================== DEBUG =================')
    print(socket_data)
    user_id = socket_data['user_id']
    lat = socket_data['lat']
    lng = socket_data['lng']

    # if user_controller.check_user_by_id(user_id):
    for rec in USERS:
        if rec['user_id'] == user_id:
            rec['lat'] = lat
            rec['lng'] = lng

    emit('markers', USERS, broadcast=True)
#
#
# @socketio.on('save-breadcrumb')
# def save_breadcrumb(socket_data):
#     # socket_data_json = json.loads(socket_data)
#
#     user_id = socket_data['user_id']
#     visit_plan_id = socket_data['visit_plan_id']
#     lat = socket_data['lat']
#     lng = socket_data['lng']
#
#     create_data = {
#         "visit_plan_id": visit_plan_id,
#         "lat": lat,
#         "lng": lng
#     }
#     result = livemap_controller.create_breadcrumb(create_data, user_id)
#
#     if result:
#         delivered_response = {
#             "error": 0,
#             "message": 'Save success breadcrumb',
#             "data": ''
#         }
#     else:
#         delivered_response = {
#             "error": 1,
#             "message": 'Failed Save breadcrumb',
#             "data": ''
#         }
#     print(delivered_response)
#     emit('response', data=delivered_response)