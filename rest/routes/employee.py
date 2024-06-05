import re
import os

from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import EmployeeController, ApprovalController, UserController

__author__ = 'junior'

bp = Blueprint(__name__, "employee")


@bp.route('/employee/<job>/import', methods=['POST'])
@jwt_required()
def import_employee_file(job):
    """
    Employee import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/branches/import"
    :endpoint:
        POST /employee/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "employee has been created"
        }
    """
    allowed_extensions = {'xls', 'xlsx'}

    user_id = current_identity.id
    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-representative']
            permissions = setting['rule'][4]
        else:
            permissions = 0

    employee_controller = EmployeeController()
    table_name = 'employee'
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
            result = employee_controller.import_employee_file(
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
            result = employee_controller.import_employee(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/employee/import', methods=['GET'])
@jwt_required()
def get_import_employee_file_list():
    """
    File employee list from staff
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/employee/import"
    :endpoint:
        POST /employee/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "area has been created"
        }
    """
    employee_controller = EmployeeController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    result = employee_controller.get_all_employee_import()

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/employee/import/<import_id>/approve', methods=['POST'])
@jwt_required()
def approve_import_employee(import_id):
    """
    Employee import approve
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/employee/import/<import_id>/approve"
    :endpoint:
        POST /employee/import/<import_id>/approve
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "area has been created"
        }
    """
    employee_controller = EmployeeController()
    user_id = current_identity.id
    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
    permission = setting['rule'][4]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-representative']
            permission = setting_group['rule'][4]
        else:
            permission = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    if permission == 3:
        get_file = employee_controller.get_import_file(import_id)
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, filename)

        result = employee_controller.import_employee(import_file, user_id)

        update_status = employee_controller.update_import_file(import_id, user_id)

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/employee', methods=['POST'])
@jwt_required()
def create_employee():
    """
    Create new employee
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "employee_data:<json>"
        "http://localhost:7091/employee"
    :endpoint:
        POST /employee
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Employee has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()
    employee_controller = EmployeeController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-representative']
            permission = setting_group['rule'][1]
        else:
            permission = 0

    is_job_function = 'sales'

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    # TODO: Get Json Data From FE
    try:
        request_data = request.get_json(silent=True)

        if request_data['job_function'] == 'supervisor' or request_data['job_function'] == 'manager':
            setting = current_identity.permissions['setting']['data']['setting-user']['data'][
                'setting-user-admin']
            permission = setting['rule'][1]

            if permission == 10:
                if current_identity.permissions_group is not None:
                    setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                        'setting-user-admin']
                    permission = setting_group['rule'][1]
                else:
                    permission = 0
            is_job_function = 'supervisor'
        if request_data['job_function'] == 'driver' or request_data['job_function'] == 'crew':
            setting = current_identity.permissions['logistic']['data']['logistic-data']['data'][
                'logistic-data-crew']
            permission = setting['rule'][1]

            if permission == 10:
                if current_identity.permissions_group is not None:
                    setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                        'logistic-data-crew']
                    permission = setting_group['rule'][1]
                else:
                    permission = 0
            is_job_function = 'logistic'

        if permission == 1:
            request_data['is_approval'] = False
            request_data['approval_by'] = None
        else:
            request_data['is_approval'] = True
            request_data['approval_by'] = user_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

    rule = {
        "name":{
            "max": 255,
            "required": True
        },
        "job_function":{
            "max": 100,
            "required": True
        },
        "email": {
            "max": 255,
            "email_format": True
        },
        "nip": {
            "max": 255,
            "required": True
        },
        "phone": {
            "max": 255
        }
    }

    field_validator = validator.validator_field(request_data, rule)
    if request_data['job_function'] == 'supervisor':
        if request_data['is_supervisor_sales'] == 0 and request_data['is_supervisor_logistic'] == 0:
            field_validator.append(
                {
                    "field": "job_function",
                    "message": "Please choose either Supervisor Sales OR Supervisor Logistic"
                }
            )

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    employee = employee_controller.create(request_data, user_id)

    if employee:
        response['error'] = 0
        response['message'] = 'Success create employee'
        if permission == 1:
            result = employee_controller.get_employee_by_id(employee)
            create_data = {
                "prefix": "employee/{}".format(is_job_function),
                "data_id": employee,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "name": result['name'],
                    "nip": result['nip'],
                    "email": result['email'],
                    "phone": result['phone'],
                    "job_function": result['job_function'],
                    "is_supervisor_sales": result['is_supervisor_sales'],
                    "is_supervisor_logistic": result['is_supervisor_logistic']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = employee_controller.rollback_insert(employee)
                print("Employee deleted")
    else:
        raise BadRequest('Failed create employee', 500, 1, data=[])

    return jsonify(response)


@bp.route('/employee', methods=["GET"])
@jwt_required()
def get_all_employee():
    """
    Get List all employee
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/employee"
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
    employee_controller = EmployeeController()
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

    employee = employee_controller.get_all_employee_data(page=page, limit=limit, search=search,
                                                         column=column, direction=direction)

    response['error'] = 0
    response['data'] = employee

    return jsonify(response)


@bp.route('/employee/sales', methods=["GET"])
@jwt_required()
def get_all_employee_sales():
    """
    Get List all employee
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/employee"
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
    employee_controller = EmployeeController()
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

    employee = employee_controller.get_all_employee_sales_data(page=page, limit=limit, search=search,
                                                               column=column, direction=direction)

    response['error'] = 0
    response['data'] = employee

    return jsonify(response)


@bp.route('/employee/collector', methods=["GET"])
@jwt_required()
def get_all_employee_collector():
    """
    Get List all employee
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/employee"
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
    employee_controller = EmployeeController()
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

    employee = employee_controller.get_all_employee_collector_data(page=page, limit=limit, search=search,
                                                               column=column, direction=direction)

    response['error'] = 0
    response['data'] = employee

    return jsonify(response)    


@bp.route('/employee/supervisor', methods=["GET"])
@jwt_required()
def get_all_employee_supervisor():
    """
    Get List all administrator
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/administrator"
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
    employee_controller = EmployeeController()
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

    employee = employee_controller.get_all_administrator_data(page=page, limit=limit, search=search,
                                                              column=column, direction=direction)

    response['error'] = 0
    response['data'] = employee

    return jsonify(response)


@bp.route('/employee/logistic', methods=["GET"])
@jwt_required()
def get_all_employee_logistic():
    """
    Get List all administrator
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/administrator"
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
    employee_controller = EmployeeController()
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

    employee = employee_controller.get_all_logistic_data(page=page, limit=limit, search=search,
                                                              column=column, direction=direction)

    response['error'] = 0
    response['data'] = employee

    return jsonify(response)


@bp.route('/employee/<job_function>/approval', methods=["GET"])
@jwt_required()
def get_all_employee_approval(job_function):
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

    if job_function == 'sales':
        setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    elif job_function == 'supervisor':
        setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-admin']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    elif job_function == 'logistic':
        setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-crew']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    else:
        raise BadRequest("Wrong Job Function Employee", 422, 1, data=[])

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
        page=page, limit=limit, search=search, column=column, direction=direction,
        prefix='employee/{}'.format(job_function), permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/employee/<employee_id>', methods=["GET"])
@jwt_required()
def get_employee_by_id(employee_id):
    """
    Get Employee Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    employee_controller = EmployeeController()
    employee = employee_controller.get_employee_by_id(employee_id)

    response['error'] = 0
    response['data'] = employee
    return jsonify(response)


@bp.route('/employee/<employee_id>', methods=["PUT"])
@jwt_required()
def update_employee(employee_id):
    """
    Update Employee Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    employee_controller = EmployeeController()
    approval_controller = ApprovalController()

    validator = Validator()
    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
    permission = setting['rule'][2]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-representative']
            permission = setting_group['rule'][2]
        else:
            permission = 0
    is_job_function = 'sales'
    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = employee_id
        if update_data['job_function'] == 'supervisor' or update_data['job_function'] == 'manager':
            setting = current_identity.permissions['setting']['data']['setting-user']['data'][
                'setting-user-admin']
            permission = setting['rule'][2]

            if permission == 10:
                if current_identity.permissions_group is not None:
                    setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                        'setting-user-admin']
                    permission = setting_group['rule'][2]
                else:
                    permission = 0
            is_job_function = 'supervisor'
        if update_data['job_function'] == 'driver' or update_data['job_function'] == 'crew':
            setting = current_identity.permissions['logistic']['data']['logistic-data']['data'][
                'logistic-data-crew']
            permission = setting['rule'][1]

            if permission == 10:
                if current_identity.permissions_group is not None:
                    setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                        'logistic-data-crew']
                    permission = setting_group['rule'][1]
                else:
                    permission = 0
            is_job_function = 'logistic'
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "name":{
            "max": 255,
            "required": True
        },
        "job_function":{
            "max": 100,
            "required": True
        },
        "email": {
            "max": 255,
            "email_format": True
        },
        "nip": {
            "max": 255,
            "required": True
        },
        "phone": {
            "max": 255
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    employee_name = update_data['name']
    if employee_controller.check_employee_by_name(employee_name, employee_id):
        field_validator.append({"field": "name", "message": "Employe name is already in use"})

    if update_data['job_function'] == 'supervisor':
        if update_data['is_supervisor_sales'] == 0 and update_data['is_supervisor_logistic'] == 0:
            field_validator.append(
                {
                    "field": "job_function",
                    "message": "Please choose either Supervisor Sales OR Supervisor Logistic"
                }
            )
    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    if permission == 1:
        edit_data = {
            "id": employee_id,
            "edit_data": update_data
        }
        try:
            employee = employee_controller.update_employee(edit_data, employee_id)

            response['error'] = 0
            response['message'] = 'Success request update employee'

            result = update_data
            create_data = {
                "prefix": "employee/{}".format(is_job_function),
                "data_id": employee_id,
                "type": "edit",
                "data": {
                    "id": result['id'],
                    "name": result['name'],
                    "nip": result['nip'],
                    "email": result['email'],
                    "phone": result['phone'],
                    "job_function": result['job_function'],
                    "is_supervisor_sales": result['is_supervisor_sales'],
                    "is_supervisor_logistic": result['is_supervisor_logistic']
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
            employee = employee_controller.update_employee(update_data, employee_id)

            response['error'] = 0
            response['message'] = 'Success update employee'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/employee/<job_function>/<employee_id>/approve', methods=["PUT"])
@jwt_required()
def update_employee_approve(job_function, employee_id):
    """
    Approve Edit employee
    :example:
    :param job_function:
    :param employee_id:
    :return:

    """
    user_id = current_identity.id
    employee_controller = EmployeeController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    if job_function == 'sales':
        setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    elif job_function == 'supervisor':
        setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-admin']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    elif job_function == 'logistic':
        setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-crew']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    else:
        raise BadRequest("Wrong Job Function Employee", 422, 1, data=[])

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    type_approve = request.get_json(silent=True)
    if type_approve['type_approve'] == 'create':
        if permission[1] == 3:
            edit_data = {
                "id": employee_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                employee = employee_controller.update_employee(edit_data, employee_id)

                response['error'] = 0
                response['message'] = 'Success approve create employee'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            employee = employee_controller.get_employee_by_id(employee_id)
            edit_data = employee['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                employee = employee_controller.update_employee(edit_data, employee_id)

                response['error'] = 0
                response['message'] = 'Success approve edit employee'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = employee_controller.get_employee_by_id(employee_id)
            count_delete = employee_controller.get_employee_delete_count(result['nip'])
            if count_delete:
                count_delete += 1
                update_data = {
                    "id": employee_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                update_data = {
                    "id": employee_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                employee = employee_controller.update_employee(update_data, employee_id)
                response['error'] = 0
                response['message'] = 'Success approve delete employee'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest('Access Not Authorized', 403, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            employee_id, type_approve['type_approve'], "employee/{}".format(job_function)
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


@bp.route('/employee/<job_function>/<employee_id>/reject', methods=["PUT"])
@jwt_required()
def update_employee_reject(job_function, employee_id):
    """
    Approve Edit employee
    :example:
    :param job_function:
    :param employee_id:
    :return:

    """
    user_id = current_identity.id
    employee_controller = EmployeeController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    if job_function == 'sales':
        setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    elif job_function == 'supervisor':
        setting = current_identity.permissions['setting']['data']['setting-user']['data']['setting-user-admin']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    elif job_function == 'logistic':
        setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-crew']
        permission = setting['rule']

        if permission[1] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[1] = setting_group['rule'][1]
            else:
                permission[1] = 0
        if permission[2] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[2] = setting_group['rule'][2]
            else:
                permission[2] = 0
        if permission[3] == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission[3] = setting_group['rule'][3]
            else:
                permission[3] = 0
    else:
        raise BadRequest("Wrong Job Function Employee", 422, 1, data=[])

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    type_approve = request.get_json(silent=True)
    if type_approve['type_approve'] == 'create':
        if permission[1] == 3:
            result = employee_controller.get_employee_by_id(employee_id)
            count_delete = employee_controller.get_employee_delete_count(result['nip'])
            if count_delete:
                count_delete += 1
                edit_data = {
                    "id": employee_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                edit_data = {
                    "id": employee_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                employee = employee_controller.update_employee(edit_data, employee_id)

                response['error'] = 0
                response['message'] = 'Success reject create employee'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": employee_id,
                "edit_data": None
            }
            try:
                employee = employee_controller.update_employee(edit_data, employee_id)

                response['error'] = 0
                response['message'] = 'Success reject edit employee'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": employee_id,
                "is_delete_approval": False
            }
            try:
                employee = employee_controller.update_employee(update_data, employee_id)
                response['error'] = 0
                response['message'] = 'Success reject delete employee'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest('Access Not Authorized', 403, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            employee_id, type_approve['type_approve'], "employee/{}".format(job_function)
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


@bp.route('/employee/<job_function>/<employee_id>', methods=["DELETE"])
@jwt_required()
def delete_employee(job_function, employee_id):
    """
    Delete employee
    :example:

    :param employee_id:
    :return:
    """
    user_id = current_identity.id
    employee_controller = EmployeeController()
    approval_controller = ApprovalController()
    user_controller = UserController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    if user_controller.check_user_by_employee(employee_id, None):
        raise BadRequest("Employee still assign into User", 422, 1, data=[])
    
    permission = 0
    if job_function == 'sales':
        setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-representative']
        permission = setting['rule'][3]

        if permission == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                    'sales-data-representative']
                permission = setting_group['rule'][3]
            else:
                permission = 0
    elif job_function == 'supervisor':
        setting = current_identity.permissions['setting']['data']['setting-user']['data'][
            'setting-user-admin']
        permission = setting['rule'][3]

        if permission == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['setting']['data']['setting-user']['data'][
                    'setting-user-admin']
                permission = setting_group['rule'][3]
            else:
                permission = 0
    elif job_function == 'logistic':
        setting = current_identity.permissions['logistic']['data']['logistic-data']['data'][
            'logistic-data-crew']
        permission = setting['rule'][3]

        if permission == 10:
            if current_identity.permissions_group is not None:
                setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                    'logistic-data-crew']
                permission = setting_group['rule'][3]
            else:
                permission = 0
    else:
        raise BadRequest("Wrong Job Function Employee", 422, 1, data=[])

    if permission == 1:
        update_data = {
            "id": employee_id,
            "is_delete_approval": True,
        }
        try:
            employee = employee_controller.update_employee(update_data, employee_id)
            response['error'] = 0
            response['message'] = 'Success request delete branch'

            result = employee_controller.get_employee_by_id(employee_id)
            create_data = {
                "prefix": "employee/{}".format(job_function),
                "data_id": employee_id,
                "type": "delete",
                "data": {
                    "id": employee_id,
                    "name": result['name'],
                    "nip": result['nip'],
                    "email": result['email'],
                    "phone": result['phone'],
                    "job_function": result['job_function'],
                    "is_supervisor_sales": result['is_supervisor_sales'],
                    "is_supervisor_logistic": result['is_supervisor_logistic']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = employee_controller.get_employee_by_id(employee_id)
        count_delete = employee_controller.get_employee_delete_count(result['nip'])
        if count_delete:
            count_delete += 1
            update_data = {
                "id": employee_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "id": employee_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            employee = employee_controller.update_employee(update_data, employee_id)
            response['error'] = 0
            response['message'] = 'Success delete employee'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)