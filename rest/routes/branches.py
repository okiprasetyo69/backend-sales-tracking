import re
import os

from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import BranchesController, ApprovalController

__author__ = 'junior'

bp = Blueprint(__name__, "branches")


@bp.route('/branches/import', methods=['POST'])
@jwt_required()
def import_branches_file():
    """
    Brnach import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/branches/import"
    :endpoint:
        POST /branches/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "branch has been created"
        }
    """
    allowed_extensions = {'xls', 'xlsx'}

    user_id = current_identity.id
    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permissions = setting['rule'][4]
        else:
            permissions = 0

    branch_controller = BranchesController()
    table_name = 'branches'
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
            result = branch_controller.import_branch_file(filename=today+'_'+filename, filename_origin=filename,
                                                     table=table_name, user_id=user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    elif permissions == 2 or permissions == 3:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            # filename = secure_filename(import_file.filename)
            # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = branch_controller.import_branch(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/branches/import', methods=['GET'])
@jwt_required()
def get_import_branch_file_list():
    """
    Sales Order import excel
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
    branch_controller = BranchesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    import_list = branch_controller.get_all_branch_import()

    response['error'] = 0
    response['data'] = import_list

    return jsonify(response)


@bp.route('/branches/import/<import_id>/approve', methods=['POST'])
@jwt_required()
def approve_import_branch(import_id):
    """
    Sales Order import excel
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
    branch_controller = BranchesController()
    user_id = current_identity.id
    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permissions = setting['rule'][4]
        else:
            permissions = 0
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if permissions == 3:
        get_file = branch_controller.get_import_file(import_id)
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, filename)

        result = branch_controller.import_branch(import_file, user_id)

        update_status = branch_controller.update_import_file(import_id, user_id)

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/branches', methods=['POST'])
@jwt_required()
def create_branches():
    """
    Create new branches
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "branches_data:<json>"
        "http://localhost:7091/branches"
    :endpoint:
        POST /branches
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "branches has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()
    branches_controller = BranchesController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permission = setting['rule'][1]
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
        },
        "branch_code": {
            "max": 2,
            "min": 2,
            "required": True
        },
        "division_id": {
            "required": True
        },
        "address": {
            "required": True
        },
        "lat":{
            "required": True,
            "numeric": True
        },
        "lng":{
            "required": True,
            "numeric": True
        }
    }

    field_validator = validator.validator_field(request_data, rule)

    branches_name = request_data['name']
    branches_code = request_data['branch_code']
    if branches_controller.check_branches_by_name(branches_name, None):
        field_validator.append({"field": "name", "message": "Branch name is already in use"})
    if branches_controller.check_branches_by_code(branches_code, None):
        field_validator.append({"field": "branch_code", "message": "Branch code is already in use"})

    if request_data.get('working_hour_start'):
        if request_data['working_hour_start']:
            time = request_data['working_hour_start'].split(":")
            hour = int(time[0].replace('_', '0'))
            minute = int(time[1].replace('_', '0'))
            if hour > 24:
                field_validator.append({"field": "working_hour_start", "message": "Hour's can't exceed more than 24"})
            if minute > 59:
                field_validator.append({"field": "working_hour_start", "message": "Minute's can't exceed more than 59"})
            request_data['working_hour_start'] = "{0}:{1}".format(hour, minute)

    if request_data.get('working_hour_end'):
        if request_data['working_hour_end']:
            time = request_data['working_hour_end'].split(":")
            hour = int(time[0].replace('_', '0'))
            minute = int(time[1].replace('_', '0'))
            if hour > 24:
                field_validator.append({"field": "working_hour_end", "message": "Hour's can't exceed more than 24"})
            if minute > 59:
                field_validator.append({"field": "working_hour_end", "message": "Minute's can't exceed more than 59"})
            request_data['working_hour_end'] = "{0}:{1}".format(hour, minute)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    branches = branches_controller.create(request_data, user_id)
    if branches:
        response['error'] = 0
        response['message'] = 'Success create branches'
        if permission == 1:
            response['message'] = 'Success request create branches'
            result = branches_controller.get_branches_by_id(branches)
            create_data = {
                "prefix": "branches",
                "data_id": branches,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "name": result['name'],
                    "branch_code": result['branch_code'],
                    "phone": result['phone'],
                    "email": result['email'],
                    "address": result['address'],
                    "lng": result['lng'],
                    "lat": result['lat'],
                    "working_day_start": result['working_day_start'],
                    "working_day_end": result['working_day_end'],
                    "working_hour_start": result['working_hour_start'],
                    "working_hour_end": result['working_hour_end'],
                    "area_id": result['area_id'],
                    "division_id": result['division_id']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = branches_controller.rollback_insert(branches)
                print("Branch deleted")
    else:
        raise BadRequest('Failed create branches', 500, 1, data=[])

    return jsonify(response)


@bp.route('/branches', methods=["GET"])
@jwt_required()
def get_all_branches():
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
    branches_controller = BranchesController()
    branch_privilege = current_identity.branch_privilege
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
    dropdown = False
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('dropdown'):
        dropdown = True

    branches = branches_controller.get_all_branches_data(
        page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown,
        branch_privilege=branch_privilege
    )

    response['error'] = 0
    response['data'] = branches

    return jsonify(response)


@bp.route('/branches/approval', methods=["GET"])
@jwt_required()
def get_all_branches_approval():
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

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='branches',
        permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/branches/cycle', methods=["GET"])
@jwt_required()
def get_all_branches_cycle():
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
    branches_controller = BranchesController()
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

    branches = branches_controller.get_all_branches_data_cycle(page=page, limit=limit, search=search,
                                                               column=column, direction=direction)

    response['error'] = 0
    response['data'] = branches

    return jsonify(response)


@bp.route('/branches/<branches_id>', methods=["GET"])
@jwt_required()
def get_branches_by_id(branches_id):
    """
    Get branches Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    # if branches_id == '1':
    #     raise BadRequest("This Branch is main company can't be edit", 500, 1, data=[])

    branches_controller = BranchesController()
    branches = branches_controller.get_branches_by_id(branches_id)

    response['error'] = 0
    response['data'] = branches
    return jsonify(response)


@bp.route('/branches/<branches_id>', methods=["PUT"])
@jwt_required()
def update_branches(branches_id):
    """
    Update branches Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    branches_controller = BranchesController()
    approval_controller = ApprovalController()

    setting_branches = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    branches_permissions = setting_branches['rule'][2]

    if branches_permissions == 10:
        if current_identity.permissions_group is not None:
            setting_branches = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            branches_permissions = setting_branches['rule'][2]
        else:
            branches_permissions = 0
    validator = Validator()

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = branches_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "name": {
            "max": 255,
            "required": True
        },
        "branch_code": {
            "max": 2,
            "min": 2,
            "required": True
        },
        "division_id": {
            "required": True
        },
        "address": {
            "required": True
        },
        "lat":{
            "required": True,
            "numeric": True
        },
        "lng":{
            "required": True,
            "numeric": True
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

    if branches_id != '1':
        # raise BadRequest("This Branch is main company can't be edit", 500, 1, data=[])
        branches_name = update_data['name']
        branches_code = update_data['branch_code']
        if branches_controller.check_branches_by_name(branches_name, branches_id):
            field_validator.append({"field": "name", "message": "Branch name is already in use"})
        if branches_controller.check_branches_by_code(branches_code, branches_id):
            field_validator.append({"field": "branch_code", "message": "Branch code is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    if branches_permissions == 1:
        edit_data = {
            "id": branches_id,
            "edit_data": update_data
        }
        try:
            branches = branches_controller.update_branches(edit_data, branches_id)

            response['error'] = 0
            response['message'] = 'Success request update branches'

            result = update_data
            if branches_id == 1:
                create_data = {
                    "prefix": "branches",
                    "data_id": branches_id,
                    "type": "edit",
                    "data": {
                        "id": branches_id,
                        "area_id": result['area_id'],
                        "division_id": result['division_id'],
                    }
                }
            else:
                create_data = {
                    "prefix": "branches",
                    "data_id": branches_id,
                    "type": "edit",
                    "data": {
                        "id": branches_id,
                        "name": result['name'],
                        "branch_code": result['branch_code'],
                        "phone": result['phone'],
                        "email": result['email'],
                        "address": result['address'],
                        "lng": result['lng'],
                        "lat": result['lat'],
                        "working_day_start": result['working_day_start'],
                        "working_day_end": result['working_day_end'],
                        "working_hour_start": result['working_hour_start'],
                        "working_hour_end": result['working_hour_end'],
                        "area_id": result['area_id'],
                        "division_id": result['division_id']
                    }
                }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    elif branches_permissions == 2 or branches_permissions == 3:
        try:
            branches = branches_controller.update_branches(update_data, branches_id)

            response['error'] = 0
            response['message'] = 'Success update branches'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/branches/<branches_id>/approve', methods=["PUT"])
@jwt_required()
def update_branches_approve(branches_id):
    """
    Approve Edit branches
    :example:
    :param branches_id:
    :return:

    """
    user_id = current_identity.id
    branches_controller = BranchesController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
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
                "id": branches_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                branches = branches_controller.update_branches(edit_data, branches_id)

                response['error'] = 0
                response['message'] = 'Success approve create branches'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            branches = branches_controller.get_branches_by_id(branches_id)
            edit_data = branches['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None

            try:
                branches = branches_controller.update_branches(edit_data, branches_id)

                response['error'] = 0
                response['message'] = 'Success approve edit branches'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = branches_controller.get_branches_by_id(branches_id)
            count_delete = branches_controller.get_branches_delete_count(result['branch_code'])
            if count_delete:
                count_delete += 1
                update_data = {
                    "id": branches_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                update_data = {
                    "id": branches_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                branches = branches_controller.update_branches(update_data, branches_id)
                response['error'] = 0
                response['message'] = 'Success approve delete branches'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            branches_id, type_approve['type_approve'], "branches"
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


@bp.route('/branches/<branches_id>/reject', methods=["PUT"])
@jwt_required()
def update_branches_reject(branches_id):
    """
    Approve Edit branches
    :example:
    :param branches_id:
    :return:

    """
    user_id = current_identity.id
    branches_controller = BranchesController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
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
            result = branches_controller.get_branches_by_id(branches_id)
            count_delete = branches_controller.get_branches_delete_count(result['branch_code'])
            if count_delete:
                count_delete += 1
                edit_data = {
                    "id": branches_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                edit_data = {
                    "id": branches_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                branches = branches_controller.update_branches(edit_data, branches_id)

                response['error'] = 0
                response['message'] = 'Success reject create branches'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": branches_id,
                "edit_data": None
            }
            try:
                branches = branches_controller.update_branches(edit_data, branches_id)

                response['error'] = 0
                response['message'] = 'Success reject edit branches'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": branches_id,
                "is_delete_approval": False
            }
            try:
                branches = branches_controller.update_branches(update_data, branches_id)
                response['error'] = 0
                response['message'] = 'Success reject delete branches'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            branches_id, type_approve['type_approve'], "branches"
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


@bp.route('/branches/<branches_id>', methods=["DELETE"])
@jwt_required()
def delete_branches(branches_id):
    """
    Delete branches
    :example:

    :param branches_id:
    :return:
    """
    user_id = current_identity.id
    branches_controller = BranchesController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-branches']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-branches']
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
            "id": branches_id,
            "is_delete_approval": True,
        }
        try:
            branches = branches_controller.update_branches(update_data, branches_id)
            response['error'] = 0
            response['message'] = 'Success request delete branch'

            result = branches_controller.get_branches_by_id(branches_id)
            create_data = {
                "prefix": "branches",
                "data_id": branches_id,
                "type": "delete",
                "data": {
                    "id": branches_id,
                    "name": result['name'],
                    "branch_code": result['branch_code'],
                    "phone": result['phone'],
                    "email": result['email'],
                    "address": result['address'],
                    "lng": result['lng'],
                    "lat": result['lat'],
                    "working_day_start": result['working_day_start'],
                    "working_day_end": result['working_day_end'],
                    "working_hour_start": result['working_hour_start'],
                    "working_hour_end": result['working_hour_end'],
                    "area_id": result['area_id'],
                    "division_id": result['division_id']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = branches_controller.get_branches_by_id(branches_id)
        count_delete = branches_controller.get_branches_delete_count(result['branch_code'])
        if count_delete:
            count_delete += 1
            update_data = {
                "id": branches_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "id": branches_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            branches = branches_controller.update_branches(update_data, branches_id)
            response['error'] = 0
            response['message'] = 'Success delete branch'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)