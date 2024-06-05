import json
import os
import re
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from sqlalchemy import func
from werkzeug.utils import secure_filename

from rest.configuration import session
from rest.controllers import UserController, ApprovalController, CustomerController
from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.models import UserModel
from rest.models.orm.employee import EmployeeModel
from rest.models.orm.user import UserModel as User

bp = Blueprint(__name__, "user")

username_validation = re.compile(r"^[a-zA-Z0-9_]+$")
email_validation = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", re.VERBOSE)


@bp.route('/user/import', methods=['POST'])
@jwt_required()
def import_user_file():
    """
    User import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/area"
    :endpoint:
        POST /user/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "User has been imported"
        }
    """
    allowed_extensions = {'xls', 'xlsx'}

    user_id = current_identity.id
    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permissions = setting['rule'][4]
        else:
            permissions = 0

    user_controller = UserController()
    table_name = 'users'
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
            import_file.save(
                os.path.join(current_app.config['UPLOAD_FOLDER'] + '/' + table_name, today + '_' + filename))
            result = user_controller.import_user_file(filename=today + '_' + filename, filename_origin=filename,
                                                      table=table_name, user_id=user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    elif permissions == 2 or permissions == 3:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            # filename = secure_filename(import_file.filename)
            # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = user_controller.import_user(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/user/import', methods=['GET'])
@jwt_required()
def get_import_file_list():
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
    user_controller = UserController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    import_list = user_controller.get_all_user_import()

    response['error'] = 0
    response['data'] = import_list

    return jsonify(response)


@bp.route('/sales/order/import/<import_id>/approve', methods=['POST'])
@jwt_required()
def approve_import(import_id):
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
    user_controller = UserController()
    user_id = current_identity.id
    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permissions = setting['rule'][4]
        else:
            permissions = 0
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if permissions == 3:
        get_file = user_controller.get_import_file(import_id, 'so')
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER'] + '/' + table_name, filename)

        result = user_controller.import_so(import_file, user_id)

        update_status = user_controller.update_import_file(import_id, user_id, 'so')

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/user', methods=["POST"])
@jwt_required()
def register():
    """
    Create new user
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "user_data:<json>"
        "http://localhost:7091/user"
    :endpoint:
        POST /user
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "User has been created"
        }
    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    validator = Validator()
    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permission = setting['rule'][1]
    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
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
        "username": {
            "max": 255,
            "required": True,
            "username_format": True
        },
        "password": {
            "max": 255,
            "required": True,
        },
        "branch_id": {
            "required": True
        },
        "division_id": {
            "required": False
        },
        "branch_privilege_id": {
            "required": True
        },
        "division_privilege_id": {
            "required": True
        }
    }
    if request_data['employee_id'] is not None:
        employee = EmployeeModel(
            session.query(EmployeeModel).filter(EmployeeModel.id == request_data['employee_id']).one()
        )
        if employee.job_function != "driver" and employee.job_function != "crew":
            rule['division_id']['required'] = True
    field_validator = validator.validator_field(request_data, rule)
    username = request_data['username']
    email = request_data['email']
    employee_id = request_data['employee_id']
    max_account_usages = int(request_data['max_account_usages'])
    if user_controller.username_already_use(username, None):
        field_validator.append({"field": "username", "message": "Username is already in use"})

    # Check Username
    # username_data = session.query(User).filter(func.lower(User.username) == func.lower(username)).all()
    # if len(username_data) != 0:
    #     field_validator.append({"field": "username", "message": "Username is already in use"})

    if user_controller.email_already_use(email, None):
        field_validator.append({"field": "email", "message": "Email is already in use"})

    if user_controller.check_user_by_employee(employee_id, None):
        field_validator.append({"field": "employee_id", "message": "Employee has been assigned to another user"})

    if max_account_usages < 1:
        field_validator.append({"field": "max_account_usages", "message": "Minimum value is 1"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    user = user_controller.create(request_data, user_id)

    if user:
        response['error'] = 0
        response['message'] = 'Success create user'
        if permission == 1:
            result = user_controller.get_user_by_id(user)
            create_data = {
                "prefix": "user",
                "data_id": user,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "username": result['username'],
                    "email": result['email'],
                    "permissions": result['permissions'],
                    "branch_privilege_id": result['branch_privilege_id'],
                    "division_privilege_id": result['division_privilege_id'],
                    "customer_id": result['customer_id'],
                    "employee_id": result['employee_id'],
                    "mobile_device_id": result['mobile_device_id'],
                    "mobile_no_id": result['mobile_no_id'],
                    "printer_device_id": result['printer_device_id'],
                    "area_id": result['area_id'],
                    "branch_id": result['branch_id'],
                    "user_group_id": result['user_group_id'],
                    "division_id": result['division_id'],
                    "handle_division_id": result['handle_division_id'],
                    "max_account_usages": result['max_account_usages']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = user_controller.rollback_user_insert(user)
                print("User deleted")
    else:
        raise BadRequest('Failed create user', 500, 1, data=[])

    return jsonify(response)


@bp.route('/user', methods=["GET"])
@jwt_required()
def user_all_list():
    """

    :return:
    """
    user_controller = UserController()
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

    user = user_controller.get_all_user_data(page=page, limit=limit, search=search, column=column, direction=direction)

    response['error'] = 0
    response['data'] = user

    return jsonify(response)


@bp.route('/user/approval', methods=["GET"])
@jwt_required()
def get_all_user_approval():
    """
    Get List all user approval
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

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='user',
        permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/user/sales', methods=["GET"])
@jwt_required()
def user_sales_all_list():
    """

    :return:
    """
    user_controller = UserController()
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege
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
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    user = user_controller.get_all_user_sales_data(
        page=page, limit=limit, search=search, column=column, direction=direction,
        branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
    )

    response['error'] = 0
    response['data'] = user

    return jsonify(response)


@bp.route('/user/logistic', methods=["GET"])
@jwt_required()
def user_logistic_all_list():
    """

    :return:
    """
    user_controller = UserController()
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
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    user = user_controller.get_all_user_logistic_data(
        page=page, limit=limit, search=search, column=column, direction=direction,
        branch_privilege=branch_privilege, data_filter=data_filter
    )

    response['error'] = 0
    response['data'] = user

    return jsonify(response)


@bp.route('/user/<id_user>', methods=["GET"])
@jwt_required()
def user_list(id_user):
    """
    list all user
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        "http://localhost:7091/user/list"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success"
            "data": list object
        }
    """
    user_controller = UserController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user = user_controller.get_user_by_id(id_user)

    response['error'] = 0
    response['data'] = user

    return jsonify(response)


@bp.route('/user/profile/<username>', methods=["GET"])
@jwt_required()
def user_profile(username):
    """
    list all user
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        "http://localhost:7091/user/list"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success"
            "data": list object
        }
    """
    user_controller = UserController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user = user_controller.get_user_data_login(username)

    data_username = user['username']
    if user['employee'] is not None:
        data_name = user['employee']['name']
        data_nip = user['employee']['nip']
    else:
        data_name = None
        data_nip = None
    if user['mobile_no'].get('device_code'):
        data_phone = user['mobile_no']['device_code']
    else:
        data_phone = None
    data_branch = user['branch']
    data_division = user['division']
    data = {
        'username': data_username,
        'name': data_name,
        'nip': data_nip,
        'phone': data_phone,
        'branch': data_branch,
        'division': data_division
    }

    response['error'] = 0
    response['data'] = data

    return jsonify(response)


@bp.route('/user/<id_user>', methods=["PUT"])
@jwt_required()
def update_user(id_user):
    """
    list all user
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        "http://localhost:7091/user/list"
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
    user_controller = UserController()
    approval_controller = ApprovalController()

    user_model = UserModel()
    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permission = setting['rule'][2]
    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permission = setting_group['rule'][2]
        else:
            permission = 0

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
        "username": {
            "max": 255,
            "required": True,
            "username_format": True
        },
        "password": {
            "max": 255
        },
        "branch_id": {
            "required": True
        },
        "division_id": {
            "required": False
        },
        "branch_privilege_id": {
            "required": True
        },
        "division_privilege_id": {
            "required": True
        }
    }
    if update_data['employee_id'] is not None:
        employee = EmployeeModel(
            session.query(EmployeeModel).filter(EmployeeModel.id == update_data['employee_id']).one()
        )
        if employee.job_function != "driver" and employee.job_function != "crew":
            rule['division_id']['required'] = True
    field_validator = validator.validator_field(update_data, rule)

    username = update_data['username']
    email = update_data['email']
    employee_id = update_data['employee_id']
    max_account_usages = int(update_data['max_account_usages'])
    if user_controller.username_already_use(username, id_user):
        field_validator.append({"field": "username", "message": "Username is already in use"})

    if user_controller.email_already_use(email, id_user):
        field_validator.append({"field": "email", "message": "Email is already in use"})

    if user_controller.check_user_by_employee(employee_id, id_user):
        field_validator.append({"field": "employee_id", "message": "Employee has been assigned to another user"})

    if max_account_usages < 1:
        field_validator.append({"field": "max_account_usages", "message": "Minimum value is 1"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    if update_data['password']:
        update_data['password'] = user_model.hash(update_data['password'])
    else:
        del update_data['password']
    del update_data['branch'], update_data['area'], update_data['branch_privilege'], update_data['division_privilege'], \
        update_data['create_date'], update_data['update_date'], update_data['employee'], update_data['mobile_device'], \
        update_data['mobile_no'], update_data['printer_device'], update_data['user_group'], update_data['customer']

    if permission == 1:
        edit_data = {
            "id": id_user,
            "edit_data": update_data
        }
        try:
            user = user_controller.update_user(edit_data, id_user)

            response['error'] = 0
            response['message'] = 'Success request update user'
            result = update_data
            create_data = {
                "prefix": "user",
                "data_id": id_user,
                "type": "edit",
                "data": {
                    "id": id_user,
                    "username": result['username'],
                    "email": result['email'],
                    "permissions": result['permissions'],
                    "branch_privilege_id": result['branch_privilege_id'],
                    "division_privilege_id": result['division_privilege_id'],
                    "customer_id": result['customer_id'],
                    "employee_id": result['employee_id'],
                    "mobile_device_id": result['mobile_device_id'],
                    "mobile_no_id": result['mobile_no_id'],
                    "printer_device_id": result['printer_device_id'],
                    "area_id": result['area_id'],
                    "branch_id": result['branch_id'],
                    "user_group_id": result['user_group_id'],
                    "division_id": result['division_id'],
                    "handle_division_id": result['handle_division_id'],
                    "max_account_usages": result['max_account_usages']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    elif permission == 2 or permission == 3:
        try:
            user = user_controller.update_user(update_data, id_user)

            response['error'] = 0
            response['message'] = 'Success update user'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/user/<id_user>/approve', methods=["PUT"])
@jwt_required()
def update_user_approve(id_user):
    """
    Approve Edit User
    :example:
    :param user_id:
    :return:

    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
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
                "id": id_user,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                user = user_controller.update_user(edit_data, id_user)

                response['error'] = 0
                response['message'] = 'Success approve create user'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            user = user_controller.get_user_by_id(id_user)
            edit_data = user['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                user = user_controller.update_user(edit_data, id_user)

                response['error'] = 0
                response['message'] = 'Success approve update user'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = user_controller.get_user_by_id(id_user)
            count_delete = user_controller.get_user_delete_count(result['username'])
            if count_delete:
                count_delete += 1
                update_data = {
                    "id": id_user,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                update_data = {
                    "id": id_user,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                result = user_controller.update_user(update_data, id_user)

                response['error'] = 0
                response['message'] = 'Success approve delete user'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            id_user, type_approve['type_approve'], "user"
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


@bp.route('/user/<id_user>/reject', methods=["PUT"])
@jwt_required()
def update_user_reject(id_user):
    """
    Approve Edit User
    :example:
    :param user_id:
    :return:

    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
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
            result = user_controller.get_user_by_id(id_user)
            count_delete = user_controller.get_user_delete_count(result['username'])
            if count_delete:
                count_delete += 1
                edit_data = {
                    "id": id_user,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                edit_data = {
                    "id": id_user,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                user = user_controller.update_user(edit_data, id_user)

                response['error'] = 0
                response['message'] = 'Success reject create user'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": id_user,
                "edit_data": None
            }
            try:
                user = user_controller.update_user(edit_data, id_user)

                response['error'] = 0
                response['message'] = 'Success reject update user'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": id_user,
                "is_delete_approval": False
            }
            try:
                result = user_controller.update_user(update_data, id_user)

                response['error'] = 0
                response['message'] = 'Success reject delete user'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            id_user, type_approve['type_approve'], "user"
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


@bp.route('/user/<id_user>', methods=["DELETE"])
@jwt_required()
def delete_user(id_user):
    """
    Delete user
    :example:

    :param id_user:
    :return:
    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-user']
    permission = setting['rule'][3]
    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-user']
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
            "id": id_user,
            "is_delete_approval": True,
        }
        try:
            result = user_controller.update_user(update_data, id_user)
            response['error'] = 0
            response['message'] = 'Success request delete user'

            result = user_controller.get_user_by_id(id_user)
            create_data = {
                "prefix": "user",
                "data_id": id_user,
                "type": "delete",
                "data": {
                    "id": id_user,
                    "username": result['username'],
                    "email": result['email'],
                    "permissions": result['permissions'],
                    "branch_privilege_id": result['branch_privilege_id'],
                    "division_privilege_id": result['division_privilege_id'],
                    "customer_id": result['customer_id'],
                    "employee_id": result['employee_id'],
                    "mobile_device_id": result['mobile_device_id'],
                    "mobile_no_id": result['mobile_no_id'],
                    "printer_device_id": result['printer_device_id'],
                    "area_id": result['area_id'],
                    "branch_id": result['branch_id'],
                    "user_group_id": result['user_group_id'],
                    "division_id": result['division_id'],
                    "handle_division_id": result['handle_division_id'],
                    "max_account_usages": result['max_account_usages']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = user_controller.get_user_by_id(id_user)
        count_delete = user_controller.get_user_delete_count(id_user)
        if count_delete:
            count_delete += 1
            update_data = {
                "id": id_user,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "id": id_user,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            result = user_controller.update_user(update_data, id_user)

            response['error'] = 0
            response['message'] = 'Success delete user'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)


@bp.route('/user/groups', methods=["POST"])
@jwt_required()
def create_user_group():
    """
    Create New User Group
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "user_group_data:<json>"
        "http://localhost:7091/user/groups"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "User Groups has been created"
        }
    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()
    validator = Validator()

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-group']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
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
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "group_name": {
            "max": 255,
            "required": True
        },
        "code": {
            "max": 255,
            "required": True,
            "alpha_num": True
        }
    }
    field_validator = validator.validator_field(request_data, rule)

    group_name = request_data['group_name']
    if user_controller.check_user_group_by_name(group_name, None):
        field_validator.append({"field": "group_name", "message": "Groups Name is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    user_group = user_controller.create_user_group(request_data, user_id)

    if user_group:
        response['error'] = 0
        response['message'] = 'Success create user group'
        if permission == 1:
            result = user_controller.get_user_group_by_id(user_group)
            create_data = {
                "prefix": "user/groups",
                "data_id": user_group,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "group_name": result['group_name'],
                    "code": result['code'],
                    "have_asset": result['have_asset'],
                    "asset": result['asset'],
                    "permissions": result['permissions']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = user_controller.rollback_user_group_insert(user_group)
                print("User group deleted")
    else:
        raise BadRequest('Failed create user group', 500, 1, data=[])

    return jsonify(response)


@bp.route('/user/groups', methods=["GET"])
@jwt_required()
def get_all_user_group():
    """
    Get List all user group
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/user/groups"
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
    user_controller = UserController()
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
    user_group = user_controller.get_all_user_group_data(
        page=page, limit=limit, search=search, column=column, direction=direction
    )

    response['error'] = 0
    response['data'] = user_group

    return jsonify(response)


@bp.route('/user/groups/approval', methods=["GET"])
@jwt_required()
def get_all_user_groups_approval():
    """
    Get List all user approval
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

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-group']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='user/groups',
        permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/user/groups/<groups_id>', methods=["GET"])
@jwt_required()
def get_groups_by_id(groups_id):
    """
    Get User Group Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_controller = UserController()
    user_group = user_controller.get_user_group_by_id(groups_id)

    response['error'] = 0
    response['data'] = user_group
    return jsonify(response)


@bp.route('/user/groups/<groups_id>', methods=["PUT"])
@jwt_required()
def update_user_groups(groups_id):
    """
    Update User Group Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    validator = Validator()
    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-group']
    permission = setting['rule'][2]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
            permission = setting_group['rule'][2]
        else:
            permission = 0

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = groups_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "group_name": {
            "max": 255,
            "required": True
        },
        "code": {
            "max": 255,
            "required": True,
            "alpha_num": True
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    group_name = update_data['group_name']
    if user_controller.check_user_group_by_name(group_name, groups_id):
        field_validator.append({"field": "group_name", "message": "Groups Nama is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    # del update_data['asset'], update_data['create_date'], update_data['update_date']
    del update_data['create_date'], update_data['update_date']

    if permission == 1:
        edit_data = {
            "id": groups_id,
            "edit_data": update_data
        }
        try:
            user_group = user_controller.update_user_groups(edit_data, groups_id)

            response['error'] = 0
            response['message'] = 'Success request update user group'
            result = update_data
            create_data = {
                "prefix": "user/groups",
                "data_id": groups_id,
                "type": "edit",
                "data": {
                    "id": groups_id,
                    "group_name": result['group_name'],
                    "code": result['code'],
                    "have_asset": result['have_asset'],
                    "asset": result['asset'],
                    "permissions": result['permissions']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    elif permission == 2 or permission == 3:
        try:
            user_group = user_controller.update_user_groups(update_data, groups_id)

            response['error'] = 0
            response['message'] = 'Success update user group'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/user/groups/<groups_id>/approve', methods=["PUT"])
@jwt_required()
def update_user_groups_approve(groups_id):
    """
    Approve Edit User Groups
    :example:
    :param groups_id:
    :return:

    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-group']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
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
                "id": groups_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                user_group = user_controller.update_user_groups(edit_data, groups_id)

                response['error'] = 0
                response['message'] = 'Success approve create user group'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            user_group = user_controller.get_user_group_by_id(groups_id)
            edit_data = user_group['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                user_group = user_controller.update_user_groups(edit_data, groups_id)

                response['error'] = 0
                response['message'] = 'Success approve edit user group'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = user_controller.get_user_group_by_id(groups_id)
            count_delete = user_controller.get_user_group_delete_count(result['group_name'])
            if count_delete:
                count_delete += 1
                update_data = {
                    "id": groups_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                update_data = {
                    "id": groups_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                result = user_controller.update_user_groups(update_data, groups_id)

                response['error'] = 0
                response['message'] = 'Success approve delete user group'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            groups_id, type_approve['type_approve'], "user/groups"
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


@bp.route('/user/groups/<groups_id>/reject', methods=["PUT"])
@jwt_required()
def update_user_groups_reject(groups_id):
    """
    Approve Edit User Groups
    :example:
    :param groups_id:
    :return:

    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-group']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
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
            result = user_controller.get_user_group_by_id(groups_id)
            count_delete = user_controller.get_user_group_delete_count(result['group_name'])
            if count_delete:
                count_delete += 1
                edit_data = {
                    "id": groups_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                edit_data = {
                    "id": groups_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                user_group = user_controller.update_user_groups(edit_data, groups_id)

                response['error'] = 0
                response['message'] = 'Success approve create user group'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": groups_id,
                "edit_data": None
            }
            try:
                user_group = user_controller.update_user_groups(edit_data, groups_id)

                response['error'] = 0
                response['message'] = 'Success approve edit user group'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": groups_id,
                "is_delete_approval": False
            }
            try:
                result = user_controller.update_user_groups(update_data, groups_id)

                response['error'] = 0
                response['message'] = 'Success approve delete user group'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            groups_id, type_approve['type_approve'], "user/groups"
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


@bp.route('/user/groups/<groups_id>', methods=["DELETE"])
@jwt_required()
def delete_user_groups(groups_id):
    """
    Get User Group Data By id
    :example:

    :return:
    """
    user_id = current_identity.id
    user_controller = UserController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-group']
    permission = setting['rule'][3]
    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                'setting-user-group']
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
            "id": groups_id,
            "is_delete_approval": True,
        }
        try:
            result = user_controller.update_user_groups(update_data, groups_id)
            response['error'] = 0
            response['message'] = 'Success request delete user'

            result = user_controller.get_user_group_by_id(groups_id)
            create_data = {
                "prefix": "user/groups",
                "data_id": groups_id,
                "type": "delete",
                "data": {
                    "id": groups_id,
                    "group_name": result['group_name'],
                    "code": result['code'],
                    "have_asset": result['have_asset'],
                    "asset": result['asset'],
                    "permissions": result['permissions']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = user_controller.get_user_group_by_id(groups_id)
        count_delete = user_controller.get_user_group_delete_count(result['group_name'])
        if count_delete:
            count_delete += 1
            update_data = {
                "id": groups_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "id": groups_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            result = user_controller.update_user_groups(update_data, groups_id)

            response['error'] = 0
            response['message'] = 'Success delete user group'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)


@bp.route('/user/add/customer/<string:customer_code>', methods=["PUT"])
@jwt_required()
def update_user_list_customer(customer_code):
    """
        update list customer from user
        :example:
            curl -i -x POST
            -H "Authorization:JWT <token>"
            "http://localhost:7091/user/<id_user>/add/customer/<customer_code>"
        :return:
            HTTP/1.1 200 OK
            Content-Type: text/javascript
            {
                "error": 0,
                "message": "success"
                "data": []
            }
        """
    user_id = current_identity.id
    user_controller = UserController()
    customer_controller = CustomerController()
    approval_controller = ApprovalController()
    user_model = UserModel()

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
        "id": {
            "required": True
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    if not customer_controller.check_customer_by_code(customer_code, None):
        field_validator.append({"field": "code", "message": "Customer is not exist"})
    if not user_controller.check_user_by_id(update_data['id']):
        field_validator.append({"field": "id", "message": "User is not exist"})
    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    user = user_controller.get_user_by_id(update_data['id'])
    id_user = user['id']

    if user['customer_id'] is not None:
        if customer_code in user['customer_id']:
            raise BadRequest('Customer is already in user list', 422, 1, data=[])
        user['customer_id'].append(customer_code)
        update_data['customer_id'] = user['customer_id']
    else:
        update_data['customer_id'] = []
        update_data['customer_id'].append(customer_code)

    try:
        user_controller.update_user(update_data, id_user)
        response['error'] = 0
        response['message'] = 'Success update list customer'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])
    return jsonify(response)
