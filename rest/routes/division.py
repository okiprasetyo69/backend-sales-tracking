import re
import os

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from datetime import datetime
from werkzeug.utils import secure_filename

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import DivisionController, ApprovalController

__author__ = 'junior'

bp = Blueprint(__name__, "division")


@bp.route('/division/import', methods=['POST'])
@jwt_required()
def import_division_file():
    """
    Division import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/division/import"
    :endpoint:
        POST /division/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "import division success"
        }
    """
    allowed_extensions = {'xls', 'xlsx'}

    user_id = current_identity.id
    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permissions = setting['rule'][4]
        else:
            permissions = 0

    division_controller = DivisionController()
    table_name = 'division'
    today = datetime.today()
    today = today.strftime("%Y%m%d")

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    import_file = request.files['files']

    if permissions == 1:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            filename = secure_filename(import_file.filename)
            import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = division_controller.import_division_file(
                filename=today+'_'+filename, filename_origin=filename, table=table_name, user_id=user_id
            )

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    elif permissions == 2 or permissions == 3:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            # filename = secure_filename(import_file.filename)
            # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = division_controller.import_division(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/division/import', methods=['GET'])
@jwt_required()
def get_import_division_file_list():
    """
    Division import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/division/import"
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
    division_controller = DivisionController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    import_list = division_controller.get_all_division_import()

    response['error'] = 0
    response['data'] = import_list

    return jsonify(response)


@bp.route('/division/import/<import_id>/approve', methods=['POST'])
@jwt_required()
def approve_import_division(import_id):
    """
    Division import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/division"
    :endpoint:
        POST /area
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "division has been created"
        }
    """
    division_controller = DivisionController()
    user_id = current_identity.id
    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permissions = setting['rule'][4]
        else:
            permissions = 0
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if permissions == 3:
        get_file = division_controller.get_import_file(import_id)
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, filename)

        result = division_controller.import_division(import_file, user_id)

        update_status = division_controller.update_import_file(import_id, user_id)

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/division', methods=['POST'])
@jwt_required()
def create_division():
    """
    Create new division
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "division_data:<json>"
        "http://localhost:7091/division"
    :endpoint:
        POST /division
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "division has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()
    division_controller = DivisionController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
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
        "division_name": {
            "max": 255,
            "required": True
        },
        "division_code": {
            "max": 2,
            "min": 2,
            "required": True
        }
    }

    field_validator = validator.validator_field(request_data, rule)

    division_name = request_data['division_name']
    division_code = request_data['division_code']
    if division_controller.check_division_by_name(division_name, None):
        field_validator.append({"field": "division_name", "message": "Division name is already in use"})
    if division_controller.check_division_by_code(division_code, None):
        field_validator.append({"field": "division_code", "message": "Division code is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    division = division_controller.create(request_data, user_id)

    if division:
        response['error'] = 0
        response['message'] = 'Success create division'
        if permission == 1:
            result = division_controller.get_division_by_id(division)
            create_data = {
                "prefix": "division",
                "data_id": division,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "division_code": result['division_code'],
                    "division_name": result['division_name']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = division_controller.rollback_insert(division)
                print("Division deleted")
    else:
        raise BadRequest('Failed create division', 500, 1, data=[])

    return jsonify(response)


@bp.route('/division', methods=["GET"])
@jwt_required()
def get_all_division():
    """
    Get List all division
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/division"
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
    division_controller = DivisionController()
    division_privilege = current_identity.division_privilege
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    if request.args.get('list'):
        list_id = request.args.get('list')
        division = division_controller.get_division_data_by_list(list_id)
    else:
        page = int(request.args.get('page'))
        limit = int(request.args.get('limit'))
        search = None
        column = None
        direction = None
        dropdown = False
        if request.args.get('search'):
            search = request.args.get('search')
        if request.args.get('order_by_column'):
            column = request.args.get('order_by_column')
            direction = request.args.get('order_direction')
        if request.args.get('dropdown'):
            dropdown = True

        division = division_controller.get_all_division_data(
            page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown,
            division_privilege=division_privilege
        )

    response['error'] = 0
    response['data'] = division

    return jsonify(response)


@bp.route('/division/approval', methods=["GET"])
@jwt_required()
def get_all_division_approval():
    """
    Get List all division
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

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='division',
        permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/division/<division_id>', methods=["GET"])
@jwt_required()
def get_division_by_id(division_id):
    """
    Get division Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    division_controller = DivisionController()
    division = division_controller.get_division_by_id(division_id)

    response['error'] = 0
    response['data'] = division
    return jsonify(response)


@bp.route('/division/<division_id>', methods=["PUT"])
@jwt_required()
def update_division(division_id):
    """
    Update division Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    division_controller = DivisionController()
    approval_controller = ApprovalController()

    setting_div = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permissions = setting_div['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting_div = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permissions = setting_div['rule'][2]
        else:
            permissions = 0
    validator = Validator()

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = division_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "division_name": {
            "max": 255,
            "required": True
        },
        "division_code": {
            "max": 2,
            "min": 2,
            "required": True
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    division_name = update_data['division_name']
    division_code = update_data['division_code']
    if division_controller.check_division_by_name(division_name, division_id):
        field_validator.append({"field": "division_name", "message": "Division name is already in use"})
    if division_controller.check_division_by_code(division_code, division_id):
        field_validator.append({"field": "division_code", "message": "Division code is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    if permissions == 1:
        edit_data = {
            "id": division_id,
            "edit_data": update_data
        }
        try:
            division = division_controller.update_division(edit_data, division_id)

            response['error'] = 0
            response['message'] = 'Success request update division'
            result = update_data
            create_data = {
                "prefix": "division",
                "data_id": division_id,
                "type": "edit",
                "data": {
                    "id": division_id,
                    "division_code": result['division_code'],
                    "division_name": result['division_name']
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
            division = division_controller.update_division(update_data, division_id)

            response['error'] = 0
            response['message'] = 'Success update division'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/division/<division_id>/approve', methods=["PUT"])
@jwt_required()
def update_division_approve(division_id):
    """
    Approve Edit division
    :example:
    :param division_id:
    :return:

    """
    user_id = current_identity.id
    division_controller = DivisionController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
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
                "id": division_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                division = division_controller.update_division(edit_data, division_id)

                response['error'] = 0
                response['message'] = 'Success approve create division'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            division = division_controller.get_division_by_id(division_id)
            edit_data = division['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                division = division_controller.update_division(edit_data, division_id)

                response['error'] = 0
                response['message'] = 'Success approve edit division'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = division_controller.get_division_by_id(division_id)
            count_delete = division_controller.get_division_delete_count(result['division_code'])
            if count_delete:
                count_delete += 1
                update_data = {
                    "id": division_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                update_data = {
                    "id": division_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                division = division_controller.update_division(update_data, division_id)

                response['error'] = 0
                response['message'] = 'Success approve delete division'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            division_id, type_approve['type_approve'], "division"
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


@bp.route('/division/<division_id>/reject', methods=["PUT"])
@jwt_required()
def update_division_reject(division_id):
    """
    Approve Edit division
    :example:
    :param division_id:
    :return:

    """
    user_id = current_identity.id
    division_controller = DivisionController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
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
            result = division_controller.get_division_by_id(division_id)
            count_delete = division_controller.get_division_delete_count(result['division_code'])
            if count_delete:
                count_delete += 1
                edit_data = {
                    "id": division_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                edit_data = {
                    "id": division_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                division = division_controller.update_division(edit_data, division_id)

                response['error'] = 0
                response['message'] = 'Success reject create division'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": division_id,
                "edit_data": None
            }
            try:
                division = division_controller.update_division(edit_data, division_id)

                response['error'] = 0
                response['message'] = 'Success reject edit division'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": division_id,
                "is_delete_approval": False
            }
            try:
                division = division_controller.update_division(update_data, division_id)

                response['error'] = 0
                response['message'] = 'Success reject delete division'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            division_id, type_approve['type_approve'], "division"
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


@bp.route('/division/<division_id>', methods=["DELETE"])
@jwt_required()
def delete_division(division_id):
    """
    Delete division
    :example:

    :param division_id:
    :return:
    """
    user_id = current_identity.id
    division_controller = DivisionController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-division']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-division']
            permission = setting['rule'][3]
        else:
            permission = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    if permission == 1:
        update_data = {
            "id": division_id,
            "is_delete_approval": True,
        }
        try:
            division = division_controller.update_division(update_data, division_id)
            response['error'] = 0
            response['message'] = 'Success request delete division'

            result = division_controller.get_division_by_id(division_id)
            create_data = {
                "prefix": "division",
                "data_id": division_id,
                "type": "delete",
                "data": {
                    "id": division_id,
                    "division_code": result['division_code'],
                    "division_name": result['division_name']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = division_controller.get_division_by_id(division_id)
        count_delete = division_controller.get_division_delete_count(result['division_code'])
        if count_delete:
            count_delete += 1
            update_data = {
                "id": division_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "id": division_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            result = division_controller.update_division(update_data, division_id)
            response['error'] = 0
            response['message'] = 'Success delete division'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)