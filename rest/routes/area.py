import re

from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity

from rest.exceptions import BadRequest
from rest.helpers import Validator
from rest.controllers import AreaController, ApprovalController

__author__ = 'junior'

bp = Blueprint(__name__, "area")


@bp.route('/area', methods=['POST'])
@jwt_required()
def create_area():
    """
    Create new area
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/area"
    :endpoint:
        POST /area
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "area has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()
    area_controller = AreaController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-config']['data']['setting-config-area']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission = setting_group['rule'][1]
        else:
            permission = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    # TODO: Get Json Data From FE
    try:
        request_data = request.get_json(silent=True)
        if permission == 1:
            request_data['is_approval'] = False
            request_data['approval_by'] = None
        else:
            request_data['is_approval'] = True
            request_data['approval_by'] = user_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

    rule = {
        "name": {
            "max": 255,
            "required": True
        }
        # },
        # "markers":{
        #     "required": True
        # }
    }

    field_validator = validator.validator_field(request_data, rule)

    # area_name = request_data['name']
    # if area_controller.check_area_by_name(area_name, None):
    #     field_validator.append({"field": "name", "message": "Area name is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    area = area_controller.create(request_data, user_id)

    if area:
        response['error'] = 0
        response['message'] = 'Success create area'
        if permission == 1:
            result = area_controller.get_area_by_id(area)
            create_data = {
                "prefix": "area",
                "data_id": area,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "name": result['name'],
                    "marker_type": result['marker_type'],
                    "marker_color": result['marker_color'],
                    "markers": result['markers'],
                    "description": result['description']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = area_controller.rollback_insert(area)
                raise BadRequest('Failed create area', 500, 1, data=[])
    else:
        raise BadRequest('Failed create area', 500, 1, data=[])

    return jsonify(response)


@bp.route('/area', methods=["GET"])
@jwt_required()
def get_all_area():
    """
    Get List all area
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/area"
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
    area_controller = AreaController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    search = None
    column = None
    direction = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')

    area = area_controller.get_all_area_data(page=page, limit=limit, search=search, column=column, direction=direction)

    response['error'] = 0
    response['data'] = area

    return jsonify(response)


@bp.route('/area/approval', methods=["GET"])
@jwt_required()
def get_all_area_approval():
    """
    Get List all area approval
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/area/approval"
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
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-config']['data']['setting-config-area']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[3] = setting_group['rule'][3]
        else:
            permission[3] = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    search = None
    column = None
    direction = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')

    result = approval_controller.get_all_approval_data(
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='area',
        permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/area/<area_id>', methods=["GET"])
@jwt_required()
def get_area_by_id(area_id):
    """
    Get area Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    area_controller = AreaController()
    area = area_controller.get_area_by_id(area_id)

    response['error'] = 0
    response['data'] = area
    return jsonify(response)


@bp.route('/area/<area_id>', methods=["PUT"])
@jwt_required()
def update_area(area_id):
    """
    Update area Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    area_controller = AreaController()
    validator = Validator()
    approval_controller = ApprovalController()

    setting_area = current_identity.permissions['setting']['data']['setting-config']['data']['setting-config-area']
    permissions = setting_area['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting_area = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permissions = setting_area['rule'][2]
        else:
            permissions = 0

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = area_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "name": {
            "max": 255,
            "required": True
        }
        # },
        # "markers":{
        #     "required": True
        # }
    }
    field_validator = validator.validator_field(update_data, rule)

    # area_name = update_data['name']
    # if area_controller.check_area_by_name(area_name, area_id):
    #     field_validator.append({"field": "name", "message": "areas name is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    if permissions == 1:
        edit_data = {
            "id": area_id,
            "edit_data": update_data
        }
        try:
            area = area_controller.update_area(edit_data, area_id)

            response['error'] = 0
            response['message'] = 'Success update area'
            result = update_data
            create_data = {
                "prefix": "area",
                "data_id": area_id,
                "type": "edit",
                "data": {
                    "id": area_id,
                    "name": result['name'],
                    "marker_type": result['marker_type'],
                    "marker_color": result['marker_color'],
                    "markers": result['markers'],
                    "description": result['description']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    elif permissions == 2 or permissions == 3:
        try:
            area = area_controller.update_area(update_data, area_id)

            response['error'] = 0
            response['message'] = 'Success update area'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/area/<area_id>/approve', methods=["PUT"])
@jwt_required()
def update_area_approve(area_id):
    """
    Approve Edit area
    :example:
    :param area_id:
    :return:

    """
    user_id = current_identity.id
    area_controller = AreaController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-config']['data']['setting-config-area']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[3] = setting_group['rule'][3]
        else:
            permission[3] = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    type_approve = request.get_json(silent=True)
    if type_approve['type_approve'] == 'create':
        if permission[1] == 3:
            edit_data = {
                "id": area_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                area = area_controller.update_area(edit_data, area_id)

                response['error'] = 0
                response['message'] = 'Success approve create area'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            area = area_controller.get_area_by_id(area_id)
            edit_data = area['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                area = area_controller.update_area(edit_data, area_id)

                response['error'] = 0
                response['message'] = 'Success approve edit area'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": area_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id
            }
            try:
                assets = area_controller.update_area(update_data, area_id)
                response['error'] = 0
                response['message'] = 'Success approve delete area'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            area_id, type_approve['type_approve'], 'area'
        )
        update_data_approval = {
            "id": result['id'],
            "is_approved": True,
            "approved_by": user_id,
            "approved_date": today
        }
        result = approval_controller.update_approval(update_data_approval)
    except Exception as e:
        print(e)
        pass
    return jsonify(response)


@bp.route('/area/<area_id>/reject', methods=["PUT"])
@jwt_required()
def update_area_reject(area_id):
    """
    Approve Edit area
    :example:
    :param area_id:
    :return:

    """
    user_id = current_identity.id
    area_controller = AreaController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-config']['data']['setting-config-area']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[3] = setting_group['rule'][3]
        else:
            permission[3] = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    type_approve = request.get_json(silent=True)
    if type_approve['type_approve'] == 'create':
        if permission[1] == 3:
            edit_data = {
                "id": area_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id
            }
            try:
                area = area_controller.update_area(edit_data, area_id)

                response['error'] = 0
                response['message'] = 'Success reject create area'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": area_id,
                "edit_data": None
            }
            try:
                area = area_controller.update_area(edit_data, area_id)

                response['error'] = 0
                response['message'] = 'Success reject edit area'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": area_id,
                "is_delete_approval": False
            }
            try:
                assets = area_controller.update_area(update_data, area_id)
                response['error'] = 0
                response['message'] = 'Success reject delete area'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            area_id, type_approve['type_approve'], 'area'
        )
        update_data_approval = {
            "id": result['id'],
            "is_rejected": True,
            "rejected_by": user_id,
            "rejected_date": today
        }
        result = approval_controller.update_approval(update_data_approval)
    except Exception as e:
        print(e)
        pass
    return jsonify(response)


@bp.route('/area/<area_id>', methods=["DELETE"])
@jwt_required()
def delete_area(area_id):
    """
    Delete area
    :example:

    :param area_id:
    :return:
    """
    user_id = current_identity.id
    area_controller = AreaController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-config']['data']['setting-config-area']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission = setting_group['rule'][3]
        else:
            permission = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    if permission == 1:
        update_data = {
            "id": area_id,
            "is_delete_approval": True,
        }
        try:
            area = area_controller.update_area(update_data, area_id)
            response['error'] = 0
            response['message'] = 'Success request delete area'
            result = area_controller.get_area_by_id(area_id)
            create_data = {
                "prefix": "area",
                "data_id": area_id,
                "type": "delete",
                "data": {
                    "id": area_id,
                    "name": result['name'],
                    "marker_type": result['marker_type'],
                    "marker_color": result['marker_color'],
                    "markers": result['markers'],
                    "description": result['description']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        update_data = {
            "id": area_id,
            "is_deleted": True,
            "is_delete_approval_by": user_id
        }
        try:
            area = area_controller.update_area(update_data, area_id)
            response['error'] = 0
            response['message'] = 'Success delete area'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)