import os
import json

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity

from rest.controllers import InboxController
from rest.exceptions import BadRequest
from rest.helpers import Validator

__author__ = 'junior'

bp = Blueprint(__name__, "inbox")


@bp.route('/inbox', methods=["GET"])
@jwt_required()
def inbox_all_list():
    """
    list all Inbox
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/inbox?page=1&limit=50"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success"
            "data": list object
        }
    """
    user_id = current_identity.id
    inbox_controller = InboxController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    tipe = None
    search = None
    column = None
    direction = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('type'):
        tipe = request.args.get('type')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')

    result = inbox_controller.get_all_inbox_data(
        page=page, limit=limit, search=search, column=column, direction=direction, tipe=tipe, user_id=user_id
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)
