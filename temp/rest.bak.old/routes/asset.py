import re
import os

from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity

from rest.exceptions import BadRequest
from rest.helpers import Validator
from rest.controllers import AssetsController, ApprovalController

__author__ = 'junior'

bp = Blueprint(__name__, "assets")


@bp.route('/assets', methods=['POST'])
@jwt_required()
def create_assets():
    """
    Create new assets
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "assets_data:<json>"
        "http://localhost:7091/assets"
    :endpoint:
        POST /assets
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "assets has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()
    assets_controller = AssetsController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['assets']['data']['assets-data']['data']['assets-data-assets']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
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
        "code": {
            'required': True,
            'max': 255
        },
        "asset_type_id": {
            'required': True
        },
        "asset_status": {
            'required': True
        },
        "name": {
            'required': True,
            'max': 255
        }
    }

    field_validator = validator.validator_field(request_data, rule)

    code = request_data['code']
    if assets_controller.check_assets_by_code(code, None):
        field_validator.append({"field": "code", "message": "Code has been used"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    assets = assets_controller.create(request_data, user_id)

    if assets:
        response['error'] = 0
        response['message'] = 'Success create assets'
        if permission == 1:
            result = assets_controller.get_assets_by_id(assets)
            create_data = {
                "prefix": "assets",
                "data_id": assets,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "code": result['code'],
                    "name": result['name'],
                    "asset_type_id": result['asset_type_id'],
                    "asset_status": result['asset_status'],
                    "notes": result['notes']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = assets_controller.rollback_insert(assets)
                raise BadRequest('Failed create assets', 500, 1, data=[])
    else:
        raise BadRequest('Failed create assets', 500, 1, data=[])

    return jsonify(response)


@bp.route('/assets', methods=["GET"])
@jwt_required()
def get_all_assets():
    """
    Get List all assets
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/assets"
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
    assets_controller = AssetsController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    tag = None
    search = None
    column = None
    direction = None
    dropdown = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('tag'):
        tag = request.args.get('tag')
    if request.args.get('dropdown'):
        dropdown = True

    assets = assets_controller.get_all_assets_data(
        page=page, limit=limit, tag=tag, search=search, column=column, direction=direction, dropdown=dropdown
    )

    response['error'] = 0
    response['data'] = assets

    return jsonify(response)


@bp.route('/assets/approval', methods=["GET"])
@jwt_required()
def get_all_assets_approval():
    """
    Get List all branches
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/branches"
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

    setting = current_identity.permissions['assets']['data']['assets-data']['data']['assets-data-assets']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='assets',
        permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/assets/<assets_id>', methods=["GET"])
@jwt_required()
def get_assets_by_id(assets_id):
    """
    Get assets Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    assets_controller = AssetsController()
    assets = assets_controller.get_assets_by_id(assets_id)

    response['error'] = 0
    response['data'] = assets
    return jsonify(response)


@bp.route('/assets/<assets_id>', methods=["PUT"])
@jwt_required()
def update_assets(assets_id):
    """
    Update assets Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    assets_controller = AssetsController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['assets']['data']['assets-data']['data']['assets-data-assets']
    permissions = setting['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permissions = setting_group['rule'][2]
        else:
            permissions = 0
    validator = Validator()

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = assets_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "code": {
            'required': True,
            'max': 255
        },
        "asset_type_id": {
            'required': True
        },
        "asset_status": {
            'required': True
        },
        "name": {
            'required': True,
            'max': 255
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    code = update_data['code']
    if assets_controller.check_assets_by_code(code, assets_id):
        field_validator.append({"field": "code", "message": "Code has been used"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    if permissions == 1:
        edit_data = {
            "id": assets_id,
            "edit_data": update_data
        }
        try:
            assets = assets_controller.update_assets(edit_data, assets_id)

            response['error'] = 0
            response['message'] = 'Success update assets'
            result = update_data
            create_data = {
                "prefix": "assets",
                "data_id": assets_id,
                "type": "edit",
                "data": {
                    "id": assets_id,
                    "code": result['code'],
                    "name": result['name'],
                    "asset_type_id": result['asset_type_id'],
                    "asset_status": result['asset_status'],
                    "notes": result['notes']
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
            assets = assets_controller.update_assets(update_data, assets_id)

            response['error'] = 0
            response['message'] = 'Success update assets'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/assets/<assets_id>/approve', methods=["PUT"])
@jwt_required()
def update_assets_approve(assets_id):
    """
    Approve Edit assets
    :example:
    :param assets_id:
    :return:

    """
    user_id = current_identity.id
    assets_controller = AssetsController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['assets']['data']['assets-data']['data']['assets-data-assets']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
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
                "id": assets_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                assets = assets_controller.update_assets(edit_data, assets_id)

                response['error'] = 0
                response['message'] = 'Success approve create assets'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            assets = assets_controller.get_assets_by_id(assets_id)
            edit_data = assets['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                assets = assets_controller.update_assets(edit_data, assets_id)

                response['error'] = 0
                response['message'] = 'Success approve edit assets'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": assets_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id
            }
            try:
                assets = assets_controller.update_assets(update_data, assets_id)
                response['error'] = 0
                response['message'] = 'Success approve delete assets'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            assets_id, type_approve['type_approve'], 'assets'
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


@bp.route('/assets/<assets_id>/reject', methods=["PUT"])
@jwt_required()
def update_assets_reject(assets_id):
    """
    Approve Edit assets
    :example:
    :param assets_id:
    :return:

    """
    user_id = current_identity.id
    assets_controller = AssetsController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['assets']['data']['assets-data']['data']['assets-data-assets']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
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
                "id": assets_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id
            }
            try:
                assets = assets_controller.update_assets(edit_data, assets_id)

                response['error'] = 0
                response['message'] = 'Success reject create assets'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": assets_id,
                "edit_data": None
            }
            try:
                assets = assets_controller.update_assets(edit_data, assets_id)

                response['error'] = 0
                response['message'] = 'Success reject edit assets'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": assets_id,
                "is_delete_approval": False
            }
            try:
                assets = assets_controller.update_assets(update_data, assets_id)
                response['error'] = 0
                response['message'] = 'Success reject assets'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            assets_id, type_approve['type_approve'], 'assets'
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


@bp.route('/assets/<assets_id>', methods=["DELETE"])
@jwt_required()
def delete_assets(assets_id):
    """
    Delete assets
    :example:

    :param assets_id:
    :return:
    """
    user_id = current_identity.id
    assets_controller = AssetsController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['assets']['data']['assets-data']['data']['assets-data-assets']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
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
            "id": assets_id,
            "is_delete_approval": True,
        }
        try:
            assets = assets_controller.update_assets(update_data, assets_id)
            response['error'] = 0
            response['message'] = 'Success request delete assets'

            result = assets_controller.get_assets_by_id(assets_id)
            create_data = {
                "prefix": "assets",
                "data_id": assets_id,
                "type": "delete",
                "data": {
                    "id": assets_id,
                    "code": result['code'],
                    "name": result['name'],
                    "asset_type_id": result['asset_type_id'],
                    "asset_status": result['asset_status'],
                    "notes": result['notes']
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
            "id": assets_id,
            "is_deleted": True,
            "is_delete_approval_by": user_id
        }
        try:
            assets = assets_controller.update_assets(update_data, assets_id)
            response['error'] = 0
            response['message'] = 'Success delete assets'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)


@bp.route('/assets/type', methods=["GET"])
@jwt_required()
def get_all_assets_type():
    """
    Get List all assets type
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/assets"
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
    assets_controller = AssetsController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 1000
    tag = None
    search = None
    column = None
    direction = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('tag'):
        tag = request.args.get('tag')

    assets = assets_controller.get_all_assets_type_data(page=page, limit=limit, tag=tag, search=search,
                                                        column=column, direction=direction)

    response['error'] = 0
    response['data'] = assets

    return jsonify(response)