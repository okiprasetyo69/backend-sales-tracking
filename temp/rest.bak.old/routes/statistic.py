import re
import json
import requests

from datetime import datetime, date
from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity

from rest.exceptions import BadRequest
from rest.helpers import Validator
from rest.controllers import StatisticController, SalesStatisticController, LogisticStatisticController

__author__ = 'junior'

bp = Blueprint(__name__, "statistic")


@bp.route('/statistic/sales/visit', methods=['GET'])
@jwt_required()
def statistic_sales_visit():
    """
    Sales performance statistic visit
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    ss_controller = SalesStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    start_date = None
    end_date = None
    user_id = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('user_id'):
        user_id = [request.args.get('user_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ss_controller.get_statistic_visit(branch_privilege, division_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/sales/activities', methods=['GET'])
@jwt_required()
def statistic_sales_activities():
    """
    Sales performance statistic activities
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    ss_controller = SalesStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    start_date = None
    end_date = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ss_controller.get_statistic_activities(branch_privilege, division_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/sales/permission_alert', methods=['GET'])
@jwt_required()
def statistic_sales_permission_alert():
    """
    Sales performance statistic permission alert
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    ss_controller = SalesStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    start_date = None
    end_date = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ss_controller.get_statistic_permission_alert(branch_privilege, division_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/sales/invoice', methods=['GET'])
@jwt_required()
def statistic_sales_invoice():
    """
    Sales performance statistic invoice vs payment
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    ss_controller = SalesStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    start_date = None
    end_date = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ss_controller.get_statistic_invoice(branch_privilege, division_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/sales/orders', methods=['GET'])
@jwt_required()
def statistic_sales_orders():
    """
    Sales performance statistic sales order and request order
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    ss_controller = SalesStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    start_date = None
    end_date = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ss_controller.get_statistic_orders(branch_privilege, division_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/sales/report', methods=['GET'])
@jwt_required()
def statistic_sales_report():
    """
    Sales performance statistic sales order and request order
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    ss_controller = SalesStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    start_date = None
    end_date = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ss_controller.get_statistic_report(branch_privilege, division_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/logistic/delivery', methods=['GET'])
@jwt_required()
def statistic_logistic_delivery():
    """
    Sales performance statistic delivery
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    ls_controller = LogisticStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    start_date = None
    end_date = None
    user_id = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('user_id'):
        user_id = [request.args.get('user_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ls_controller.get_statistic_delivery(branch_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/logistic/report', methods=['GET'])
@jwt_required()
def statistic_logistic_report():
    """
    Sales performance statistic report
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    ls_controller = LogisticStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    start_date = None
    end_date = None
    user_id = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('user_id'):
        user_id = [request.args.get('user_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ls_controller.get_statistic_report(branch_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/logistic/packing_slip', methods=['GET'])
@jwt_required()
def statistic_logistic_packing_slip():
    """
    Sales performance statistic packing slip
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/sales
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    ls_controller = LogisticStatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    start_date = None
    end_date = None
    user_id = None
    if request.args.get('branch_id'):
        branch_privilege = [request.args.get('branch_id')]
    if request.args.get('user_id'):
        user_id = [request.args.get('user_id')]
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = ls_controller.get_statistic_packing_slip(branch_privilege, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/statistic/<job>/performance', methods=['GET'])
@jwt_required()
def statistic_performance_list_user(job):
    """
    Sales performance statistic by user_ids
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "create_data:<json>"
        "http://localhost:7091/statistic/sales"
    :endpoint:
        POST /statistic/performance
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "log activity has been created"
        }
    """
    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    statistic_controller = StatisticController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_ids = json.loads(request.args.get('user_id'))
    if not user_ids:
        raise BadRequest('Please input minimal one id user', 422, 1, data=[])
    today = date.today()
    todays = today.strftime("%Y-%m-%d")
    start_date = todays
    end_date = todays
    if request.args.get('start_date'):
        start_date = request.args.get('start_date')
    if request.args.get('end_date'):
        end_date = request.args.get('end_date')

    result = statistic_controller.get_statistic_performance_by_user_id(job, user_ids, start_date, end_date)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)
