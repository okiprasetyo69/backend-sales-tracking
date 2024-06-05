import re
import json

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity

from rest.exceptions import BadRequest
from rest.helpers import Validator
from rest.controllers import SettingController, BranchesController

__author__ = 'junior'

bp = Blueprint(__name__, "setting")


# TODO: Endpoint For Setting Company Profile
@bp.route('/setting/company', methods=["GET"])
@jwt_required()
def get_company_profile():
    """
    Get data company profile
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/company"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()
    company_id = 1
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    company = setting_controller.get_company_by_id(company_id)

    response['error'] = 0
    response['data'] = company

    return jsonify(response)


@bp.route('/setting/company', methods=["PUT"])
@jwt_required()
def update_company_profile():
    """
    Get data company profile
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/company"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()
    branch_controller = BranchesController()
    validator = Validator()
    company_id = 1

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "name": {
            "max": 255,
            "required": True
        },
        "phone": {
            "max": 255
        },
        "email": {
            "max": 255
        },
        "working_day_start": {
            "max": 255
        },
        "working_day_end": {
            "max": 255
        },
        "branch_code": {
            "max": 2,
            "required": True
        },
        "lat": {
            "required": True,
            "numeric": True
        },
        "lng": {
            "required": True,
            "numeric": True
        },
        "address": {
            "required": True
        }
    }

    field_validator = validator.validator_field(update_data, rule)

    if update_data.get('working_hour_start'):
        if update_data['working_hour_start']:
            time = update_data['working_hour_start'].split(":")
            hour = int(time[0].replace('_', '0'))
            minute = int(time[1].replace('_', '0'))
            if hour > 24:
                field_validator.append({"field": "working_hour_start", "message": "Hour's can't exceed more than 24"})
            if minute > 59:
                field_validator.append({"field": "working_hour_start", "message": "Minute's can't exceed more than 59"})
            update_data['working_hour_start'] = "{0}:{1}".format(hour, minute)

    if update_data.get('working_hour_end'):
        if update_data['working_hour_end']:
            time = update_data['working_hour_end'].split(":")
            hour = int(time[0].replace('_', '0'))
            minute = int(time[1].replace('_', '0'))
            if hour > 24:
                field_validator.append({"field": "working_hour_end", "message": "Hour's can't exceed more than 24"})
            if minute > 59:
                field_validator.append({"field": "working_hour_end", "message": "Minute's can't exceed more than 59"})
            update_data['working_hour_end'] = "{0}:{1}".format(hour, minute)

    branch_code = update_data['branch_code']
    if branch_controller.check_branches_by_code(branch_code, 1):
        field_validator.append({"field": "branch_code", "message": "Branches code is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    try:
        company = setting_controller.update_company(update_data, company_id)
        company = setting_controller.get_company_by_id(company_id)
        try:
            branch_data = dict()
            branch_data['id'] = 1
            branch_data['name'] = update_data['name']
            branch_data['branch_code'] = update_data['branch_code']
            branch_data['email'] = update_data['email']
            branch_data['phone'] = update_data['phone']
            branch_data['address'] = update_data['address']
            branch_data['nfcid'] = update_data['nfcid']
            branch_data['lng'] = update_data['lng']
            branch_data['lat'] = update_data['lat']
            branches = branch_controller.update_branches(update_data, 1)
        except:
            print('failed update branch')
        response['error'] = 0
        response['message'] = 'Success update company'
        response['data'] = company
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)


# TODO: Endpoint For Setting General
@bp.route('/setting/general', methods=["GET"])
@jwt_required()
def get_setting_general():
    """
    Get data setting general
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/setting/general"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()
    general_id = 1
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    general = setting_controller.get_general_by_id(general_id)

    response['error'] = 0
    response['data'] = general

    return jsonify(response)


@bp.route('/setting/general', methods=["PUT"])
@jwt_required()
def update_general():
    """
    Update data setting general
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/setting/general"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()
    validator = Validator()
    general_id = 1

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = general_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)
    rule = {}
    field_validator = validator.validator_field(update_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    try:
        general = setting_controller.update_general(update_data, general_id)
        general = setting_controller.get_general_by_id(general_id)
        response['error'] = 0
        response['message'] = 'Success update general'
        response['data'] = general
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)


# TODO: Endpoint For Setting Notifications
@bp.route('/setting/notif/type/<type>', methods=["GET"])
@jwt_required()
def get_all_setting_notif(type):
    """
    Get data setting notifications by category
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/setting/general"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    notif = setting_controller.get_all_notif_data(type)

    response['error'] = 0
    response['data'] = notif

    return jsonify(response)


@bp.route('/setting/notif/<notif_id>', methods=["GET"])
@jwt_required()
def get_setting_notif(notif_id):
    """
    Get data setting general
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/setting/notif/<notif_id>"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    notif = setting_controller.get_notif_by_id(notif_id)

    response['error'] = 0
    response['data'] = notif

    return jsonify(response)


@bp.route('/setting/notif/<notif_id>', methods=["PUT"])
@jwt_required()
def update_notif(notif_id):
    """
    Update data setting general
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/setting/general"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()
    validator = Validator()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = notif_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)
    rule = {}
    field_validator = validator.validator_field(update_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    try:
        notif = setting_controller.update_notif(update_data, notif_id)
        response['error'] = 0
        response['message'] = 'Success update notification setting'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)


# TODO: Endpoint For Generate Unique Number
@bp.route('/print/unique/code', methods=["GET"])
@jwt_required()
def get_print_unique_code():
    """
    Get data setting general
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/setting/general"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    random_code = setting_controller.get_print_unique_code()

    response['error'] = 0
    response['data'] = random_code

    return jsonify(response)


@bp.route('/print/unique/code/check', methods=["POST"])
@jwt_required()
def check_print_unique_code():
    """
    Get data setting general
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/setting/general"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": ""
            "data": {
                "has_next":<boolean>,
                "has_prev":<boolean>,
                "total":<int>,
                "data":<list object>
            }
        }
    """
    setting_controller = SettingController()
    validator = Validator()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "date": {
            "required": True
        },
        "code": {
            "required": True,
            "numeric": True,
        }
    }

    field_validator = validator.validator_field(update_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    result = setting_controller.check_print_unique_code(update_data)

    if result:
        response['error'] = 0
        response['data'] = "Code is valid"
    else:
        response['error'] = 1
        response['data'] = "Code is invalid"

    return jsonify(response)
