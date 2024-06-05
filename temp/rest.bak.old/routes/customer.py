import re
import os
import json
import pandas as pd

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename
from datetime import datetime
from ast import literal_eval

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import CustomerController, ApprovalController, UserController, AreaController
from rest.models import UserModel

__author__ = 'junior'

bp = Blueprint(__name__, "customer")


def __init__(self):
    self.user_model = UserModel()


@bp.route('/customer/import', methods=['POST'])
@jwt_required()
def import_customer_file():
    """
    Customer import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "files:<file>"
        "http://localhost:7091/customer/import"
    :endpoint:
        POST /customer/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Import Success"
        }
    """
    allowed_extensions = {'xls', 'xlsx'}
    user_id = current_identity.id
    sales_customer = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permissions = sales_customer['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            sales_customer = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permissions = sales_customer['rule'][4]
        else:
            permissions = 0

    customer_controller = CustomerController()
    table_name = 'customer'
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
            result = customer_controller.import_customer_file(filename=today + '_' + filename, filename_origin=filename,
                                                              table=table_name, user_id=user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    elif permissions == 2 or permissions == 3:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            # filename = secure_filename(import_file.filename)
            # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = customer_controller.import_customer(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/customer/import', methods=['GET'])
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
    customer_controller = CustomerController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    import_list = customer_controller.get_all_customer_import()

    response['error'] = 0
    response['data'] = import_list

    return jsonify(response)


@bp.route('/customer/import/<import_id>/approve', methods=['POST'])
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
    customer_controller = CustomerController()
    user_id = current_identity.id
    sales_customer = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permissions = sales_customer['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            sales_customer = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permissions = sales_customer['rule'][4]
        else:
            permissions = 0
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if permissions == 3:
        get_file = customer_controller.get_import_file(import_id)
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER'] + '/' + table_name, filename)

        result = customer_controller.import_customer(import_file, user_id)

        update_status = customer_controller.update_import_file(import_id, user_id)

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/customer', methods=['POST'])
@jwt_required()
def create_customer():
    """
    Create new customer
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "division_data:<json>"
        "http://localhost:7091/customer"
    :endpoint:
        POST /customer
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
    customer_controller = CustomerController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
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
        raise BadRequest("Params is missing or error format, check double quatation", 422, 1, data=[])

    rule = {
        "username": {
            "max": 255,
            "username_format": True
        },
        "password": {
            "max": 255,
        },
        "name": {
            "max": 255,
            "required": True,
            "safe_format": True,
        },
        "phone": {
            "max": 255
        },
        "email": {
            "max": 255,
            "email_format": True
        },
        "code": {
            "max": 255,
            "required": True,
            "code_format": True,
            # "alpha_num": True
        },
        "lat": {
            "required": True,
            "numeric": True
        },
        "lng": {
            "required": True,
            "numeric": True
        },
        "contacts": {
            "required": True
        }
    }

    field_validator = validator.validator_field(request_data, rule)

    customer_code = request_data['code']
    # customer_username = request_data['username']
    # customer_nfcid = request_data['nfcid']
    if customer_controller.check_customer_by_code(customer_code, None):
        field_validator.append({"field": "code", "message": "Customer code is already in use"})
    # if customer_controller.check_customer_by_username(customer_username, None):
    #     field_validator.append({"field": "username", "message": "Username is already in use"})
    # if customer_controller.check_customer_by_nfcid(customer_nfcid, None):
    #     field_validator.append({"field": "nfcid", "message": "Nfcid is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    customer = customer_controller.create(request_data, user_id)

    if customer:
        response['error'] = 0
        response['message'] = 'Success create customer'
        if permission == 1:
            result = customer_controller.get_customer_by_id(customer)
            create_data = {
                "prefix": "customer",
                "data_id": customer,
                "type": "create",
                "data": {
                    "code": result['code'],
                    "name": result['name'],
                    "email": result['email'],
                    "phone": result['phone'],
                    "address": result['address'],
                    "lng": result['lng'],
                    "lat": result['lat'],
                    "username": result['username'],
                    "password": result['password'],
                    "nfcid": result['code'],
                    "contacts": result['contacts'],
                    "business_activity": result['business_activity'],
                    "is_branch": result['is_branch'],
                    "parent_code": result['parent_code']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
                result = customer_controller.rollback_insert(customer)
                print("Branch deleted")
    else:
        raise BadRequest('Failed create customer', 500, 1, data=[])

    return jsonify(response)


@bp.route('/customer', methods=["GET"])
@jwt_required()
def get_all_customer():
    """
    Get List all customer
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/customer"
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
    customer_controller = CustomerController()
    user_controller = UserController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege
    job_function = current_identity.job_function
    is_supervisor_sales = current_identity.is_supervisor_sales
    is_supervisor_logistic = current_identity.is_supervisor_logistic

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
    if request.args.get('dropdown'):
        if job_function == 'supervisor':
            if is_supervisor_sales == 1 and is_supervisor_logistic == 0:
                category = 'sales'
            elif is_supervisor_sales == 0 and is_supervisor_logistic == 1:
                category = 'logistic'
            elif is_supervisor_sales == 1 and is_supervisor_logistic == 1:
                category = 'all'
            else:
                raise BadRequest(
                    "Can't view list customer, only with assign supervisor sales or logistic", 422, 1, data=[]
                )
        dropdown = True
        # Limit for Search Dropdown Destination
        limit = int(20)

        list_customer = user_controller.get_customer_from_supervisor(
            branch_privilege=branch_privilege, division_privilege=division_privilege, category=category
        )
    else:
        list_customer = []
        dropdown = False

    customer = customer_controller.get_all_customer_data(
        page=page, limit=limit, search=search, column=column, direction=direction, list_customer=list_customer,
        dropdown=dropdown
    )

    response['error'] = 0
    response['data'] = customer

    return jsonify(response)


@bp.route('/customer/approval', methods=["GET"])
@jwt_required()
def get_all_customer_approval():
    """
    Get List all customer
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

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='customer',
        permission=permission
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/customer/parent', methods=["GET"])
@jwt_required()
def get_all_customer_parent():
    """
    Get List all customer
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/customer/parent"
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
    customer_controller = CustomerController()
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
    customer = customer_controller.get_all_customer_parent(page=page, limit=limit, search=search,
                                                           column=column, direction=direction)

    response['error'] = 0
    response['data'] = customer

    return jsonify(response)


@bp.route('/customer/check/nearby', methods=["GET"])
@jwt_required()
def get_all_customer_nearby():
    """
    Get List all customer
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/customer"
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
    customer_controller = CustomerController()
    user_controller = UserController()
    user_id = current_identity.id

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    lng = request.args.get('lng')
    lat = request.args.get('lat')
    search = None
    distance = 0.1
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('distance'):
        distance = request.args.get('distance')

    try:
        user = user_controller.get_user_by_id(user_id)
        list_customer = user['customer_id']
    except Exception as e:
        raise BadRequest(e, 422, 1, data=[])
    if not list_customer and user_id != 1:
        raise BadRequest("User doesn't have customer", 422, 1, data=[])

    customer = customer_controller.get_all_customer_nearby_data(
        page=page, limit=limit, search=search, distance=distance, lng=lng, lat=lat, list_customer=list_customer
    )

    response['error'] = 0
    response['data'] = customer

    return jsonify(response)


@bp.route('/customer/<job_function>/report', methods=['GET'])
@jwt_required()
def get_all_customer_report(job_function):
    """
    Get List Sales Invoice
    :return:
    """
    customer_controller = CustomerController()
    area_controller = AreaController()
    user_controller = UserController()

    user_id = current_identity.id
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege
    job_supervisor_function = current_identity.job_function
    is_supervisor_sales = current_identity.is_supervisor_sales
    is_supervisor_logistic = current_identity.is_supervisor_logistic

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    search = None
    data_filter = None
    result_area = []
    list_area = []
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)
        data_filter = data_filter[0]
    if user_id > 1:
        if job_supervisor_function == 'supervisor':
            if is_supervisor_sales == 1 and is_supervisor_logistic == 0:
                category = 'sales'
            elif is_supervisor_sales == 0 and is_supervisor_logistic == 1:
                category = 'logistic'
            elif is_supervisor_sales == 1 and is_supervisor_logistic == 1:
                category = 'all'
            else:
                raise BadRequest(
                    "Can't view report customer, only with assign supervisor sales or logistic", 422, 1, data=[]
                )

            list_customer = user_controller.get_customer_from_supervisor(
                branch_privilege=branch_privilege, division_privilege=division_privilege, category=category
            )
        else:
            raise BadRequest(
                "Can't view report customer, only with assign supervisor sales or logistic", 422, 1, data=[]
            )
    else:
        list_customer = True
    if data_filter:
        if data_filter['area']:
            list_polygon_area = []
            for area_id in literal_eval(data_filter['area']):
                try:
                    polygon_area = area_controller.get_area_by_id(area_id)
                    if polygon_area:
                        # add list area
                        list_area.append(polygon_area)
                        # Construct for polygon area
                        list_markers = []
                        markers = polygon_area['markers']
                        for mark in markers:
                            list_markers.append(str(mark['lat']) + ' ' + str(mark['lng']))
                        if list_markers:
                            list_markers.append(list_markers[0])
                            list_polygon_area.append("(({0}))".format(", ".join(x for x in list_markers)))
                except Exception as e:
                    # raise BadRequest(e, 422, 1, data=[])
                    # print(e)
                    pass

            if list_polygon_area:
                try:
                    result_area = customer_controller.get_all_customer_by_area(list_polygon_area, job_function,
                                                                               data_filter)
                except Exception as e:
                    raise BadRequest(e, 422, 1, data=[])
    #
    # result = customer_controller.get_all_customer_report(
    #     search=search, customer_id=result_area, branch_privilege=branch_privilege,
    #     division_privilege=division_privilege, data_filter=data_filter
    # )
    #
    if result_area and list_customer:
        if user_id > 1:
            filter_customer = [i for i in result_area if i in list_customer]
        else:
            filter_customer = result_area

        customer = customer_controller.get_all_customer_report(
            list_customer=filter_customer, data_filter=data_filter, job_function=job_function, search=search
        )

        if customer:
            if customer['data'] is not None:
                customer['data']['area'] = list_area
        response['error'] = 0
        response['data'] = customer
    else:
        response['error'] = 0
        response['message'] = "No customer in this area"
        response['data'] = []

    return jsonify(response)


@bp.route('/customer/<customer_id>', methods=["GET"])
@jwt_required()
def get_customer_by_id(customer_id):
    """
    Get customer Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    customer_controller = CustomerController()
    customer = customer_controller.get_customer_by_id(customer_id)

    response['error'] = 0
    response['data'] = customer
    return jsonify(response)


@bp.route('/customer/<customer_id>', methods=["PUT"])
@jwt_required()
def update_customer(customer_id):
    """
    Update customer Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    customer_controller = CustomerController()
    approval_controller = ApprovalController()

    validator = Validator()
    sales_customer = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permissions = sales_customer['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            sales_customer = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permissions = sales_customer['rule'][2]
        else:
            permissions = 0

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['code'] = customer_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 422, 1)

    rule = {
        "username": {
            "max": 255,
            "username_format": True
        },
        "password": {
            "max": 255,
        },
        "name": {
            "max": 255,
            "required": True,
            "safe_format": True,
        },
        "phone": {
            "max": 255
        },
        "email": {
            "max": 255,
            "email_format": True
        },
        "code": {
            "max": 255,
            "required": True,
            "code_format": True,
            # "alpha_num": True
        },
        "lat": {
            "required": True,
            "numeric": True
        },
        "lng": {
            "required": True,
            "numeric": True
        },
        "contacts": {
            "required": True
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    customer_code = update_data['code']
    # customer_username = request_data['username']
    # customer_nfcid = request_data['nfcid']
    if customer_controller.check_customer_by_code(customer_code, customer_id):
        field_validator.append({"field": "code", "message": "Customer code is already in use"})
    # if customer_controller.check_customer_by_username(customer_username, customer_id):
    #     field_validator.append({"field": "username", "message": "Username is already in use"})
    # if customer_controller.check_customer_by_nfcid(customer_nfcid, customer_id):
    #     field_validator.append({"field": "nfcid", "message": "Nfcid is already in use"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    # del update_data['branch']

    if permissions == 1:
        edit_data = {
            "code": customer_id,
            "edit_data": update_data
        }
        try:
            result = customer_controller.update_customer(edit_data, customer_id)

            response['error'] = 0
            response['message'] = 'Success request update customer'
            result = update_data
            create_data = {
                "prefix": "customer",
                "data_id": customer_id,
                "type": "edit",
                "data": {
                    "code": customer_id,
                    "name": result['name'],
                    "email": result['email'],
                    "phone": result['phone'],
                    "address": result['address'],
                    "lng": result['lng'],
                    "lat": result['lat'],
                    "username": result['username'],
                    "password": result['password'],
                    "nfcid": result['code'],
                    "contacts": result['contacts'],
                    "business_activity": result['business_activity'],
                    "is_branch": result['is_branch'],
                    "parent_code": result['parent_code']
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
            result = customer_controller.update_customer(update_data, customer_id)

            response['error'] = 0
            response['message'] = 'Success update customer'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/customer/<customer_id>/approve', methods=["PUT"])
@jwt_required()
def update_customer_approve(customer_id):
    """
    Approve Edit customer
    :example:
    :param division_id:
    :return:

    """
    user_id = current_identity.id
    customer_controller = CustomerController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
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
                "code": customer_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                result = customer_controller.update_customer(edit_data, customer_id)

                response['error'] = 0
                response['message'] = 'Success approve create customer'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            customer = customer_controller.get_customer_by_id(customer_id)
            edit_data = customer['edit_data']
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                result = customer_controller.update_customer(edit_data, customer_id)

                response['error'] = 0
                response['message'] = 'Success approve edit customer'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "code": customer_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id
            }
            try:
                result = customer_controller.update_customer(update_data, customer_id)
                response['error'] = 0
                response['message'] = 'Success approve delete customer'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            customer_id, type_approve['type_approve'], "customer"
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


@bp.route('/customer/<customer_id>/reject', methods=["PUT"])
@jwt_required()
def update_customer_reject(customer_id):
    """
    Approve Edit customer
    :example:
    :param division_id:
    :return:

    """
    user_id = current_identity.id
    customer_controller = CustomerController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
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
                "code": customer_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id
            }
            try:
                result = customer_controller.update_customer(edit_data, customer_id)

                response['error'] = 0
                response['message'] = 'Success reject create customer'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "code": customer_id,
                "edit_data": None
            }
            try:
                result = customer_controller.update_customer(edit_data, customer_id)

                response['error'] = 0
                response['message'] = 'Success reject edit customer'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "code": customer_id,
                "is_delete_approval": False
            }
            try:
                result = customer_controller.update_customer(update_data, customer_id)
                response['error'] = 0
                response['message'] = 'Success reject delete customer'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            customer_id, type_approve['type_approve'], "customer"
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


@bp.route('/customer/<customer_id>', methods=["DELETE"])
@jwt_required()
def delete_customer(customer_id):
    """
    Delete customer
    :example:

    :param customer_id:
    :return:
    """
    user_id = current_identity.id
    customer_controller = CustomerController()
    approval_controller = ApprovalController()
    user_controller = UserController()

    setting = current_identity.permissions['setting']['data']['setting-data']['data']['setting-data-customers']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['setting']['data']['setting-data']['data'][
                'setting-data-customers']
            permission = setting['rule'][3]
        else:
            permission = 0

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    # Code By Rendy Ichtiar For Delete Customer On User
    data_customer_user = user_controller.get_user_customer(customer_id)
    if data_customer_user:
        for datax in data_customer_user:
            customer_id_new = literal_eval(datax['customer_id'])
            customer_id_new.remove(customer_id)
            edit_data = {
                "id": datax['id'],
                "customer_id": customer_id_new
            }
            update_user_customer = user_controller.update_user_customer(edit_data, datax['id'])
    # EOF Code By Rendy Ichtiar

    if permission == 1:
        update_data = {
            "code": customer_id,
            "is_delete_approval": True,
        }
        try:
            result = customer_controller.update_customer(update_data, customer_id)
            response['error'] = 0
            response['message'] = 'Success request delete branch'

            result = customer_controller.get_customer_by_id(customer_id)
            create_data = {
                "prefix": "customer",
                "data_id": customer_id,
                "type": "delete",
                "data": {
                    "code": customer_id,
                    "name": result['name'],
                    "email": result['email'],
                    "phone": result['phone'],
                    "address": result['address'],
                    "lng": result['lng'],
                    "lat": result['lat'],
                    "username": result['username'],
                    "password": result['password'],
                    "nfcid": result['code'],
                    "contacts": result['contacts'],
                    "business_activity": result['business_activity'],
                    "is_branch": result['is_branch'],
                    "parent_code": result['parent_code']
                }
            }
            try:
                result = approval_controller.create(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = customer_controller.get_customer_by_id(customer_id)
        count_delete = customer_controller.get_customer_delete_count(result['code'])
        if count_delete:
            count_delete += 1
            update_data = {
                "code": customer_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "code": customer_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            result = customer_controller.update_customer(update_data, customer_id)
            response['error'] = 0
            response['message'] = 'Success delete customer'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])

    return jsonify(response)
