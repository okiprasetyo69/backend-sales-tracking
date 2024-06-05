import re
import os
import json
import pandas as pd

from flask import Blueprint, jsonify, request, current_app, make_response, send_file, render_template
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Message

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file, USERS_NOTIF, mail
from rest.controllers import SalesController, UserController, InboxController, SettingController
from rest.helpers import fcm, socketio

__author__ = 'junior'

bp = Blueprint(__name__, "sales")


# TODO: ========================Section Sales Request Order===================
@bp.route('/sales/request', methods=["POST"])
@jwt_required()
def add_request_order():
    """
    Create new request order
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "user_data:<json>"
        "http://localhost:7091/sales/request"
    :endpoint:
        POST /sales/request
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": 'Success create request order'
        }
    """
    user_id = current_identity.id
    sales_controller = SalesController()
    user_controller = UserController()
    inbox_controller = InboxController()
    validator = Validator()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        request_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

    rule = {
    }

    field_validator = validator.validator_field(request_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    result = sales_controller.create_request_order(request_data, user_id)

    if result:
        response['error'] = 0
        response['message'] = 'Success create request order'
        request_order = sales_controller.get_request_order_by_id(result)

        notif_title = "Request Order"
        notif_body = "Request order dengan Customer Code: {0}, Customer Name: {1} telah dibuat".format(
            request_order['customer_code'], request_order['customer']['name']
        )
        notif_data = {
            'title': notif_title,
            'text': notif_body
        }
        try:
            list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
            device_ids = []
            if list_supervisor:
                list_supervisor.append(1)
                token = user_controller.get_device_token_by_list_id(list_supervisor)
                if token:
                    for rec in token:
                        device_ids.append(rec['token'])

                for rec in list_supervisor:
                    create_data = {
                        'title': notif_title,
                        'message': notif_body,
                        'category': 'activities',
                        'user_id': rec,
                        'from_id': request_order['user_id'],
                        'payload': None
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass

                    message = None
                    # if user_controller.check_user_by_id(user_id):
                    for res in USERS_NOTIF:
                        if res['user_id'] == rec:
                            res['total'] += 1
                            message = res
                    if message:
                        pass
                    else:
                        USERS_NOTIF.append({
                            "user_id": rec,
                            "total": 1
                        })
                        message = {
                            "user_id": rec,
                            "total": 1
                        }

                    socketio.emit('notif-{}'.format(rec), [message], broadcast=True)

            fcm.notify_multiple_devices(
                registration_ids=device_ids,
                message_title=notif_title,
                message_body=notif_body,
                data_message=notif_data
            )
        except Exception as e:
            print(e)
            pass
    else:
        raise BadRequest('Failed create permission and alert', 500, 1, data=[])

    response = {
        'error': 0,
        'message': 'Success create request order',
        'data': []
    }

    return jsonify(response)


@bp.route('/sales/request', methods=['GET'])
@jwt_required()
def get_all_sales_request():
    """
    Get List Sales Request Order
    :return:
    """
    sales_controller = SalesController()

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
    customer_code = None
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('customer_code'):
        customer_code = request.args.get('customer_code')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    request_order = sales_controller.get_all_sales_request_data(
        page=page, limit=limit, search=search, column=column, direction=direction, customer_code=customer_code,
        branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
    )

    response['error'] = 0
    response['data'] = request_order

    return jsonify(response)


@bp.route('/sales/request/export', methods=['GET'])
@jwt_required()
def export_all_sales_request():
    """
    Get List Sales Request Order
    :return:
    """
    sales_controller = SalesController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    customer_code = None
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('customer_code'):
        customer_code = request.args.get('customer_code')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = sales_controller.get_all_export_sales_request_data(
        page=page, limit=limit, search=search, column=column, direction=direction, customer_code=customer_code,
        branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date'] and not data_filter['user_id']:
            filename = 'Report_Request_Order_all_{0}_{1}.xlsx'.format(data_filter['start_date'], data_filter['end_date'])
        elif data_filter['user_id'] and not data_filter['start_date']:
            filename = 'Report_Request_Order_{0}_all.xlsx'.format(data_filter['user_id'])
        else:
            filename = 'Report_Request_Order_{0}_{1}_{2}.xlsx'.format(
                data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
            )
    else:
        filename = 'Report_Request_Order_all.xlsx'

    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/request/export/pdf', methods=['GET'])
@jwt_required()
def export_pdf_all_sales_request():
    """
    Get List Sales Request Order
    :return:
    """
    sales_controller = SalesController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    customer_code = None
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('customer_code'):
        customer_code = request.args.get('customer_code')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = sales_controller.get_all_export_pdf_sales_request_data(
        page=page, limit=limit, search=search, column=column, direction=direction, customer_code=customer_code,
        branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date'] and not data_filter['user_id']:
            filename = 'Report_Request_Order_all_{0}_{1}.pdf'.format(data_filter['start_date'], data_filter['end_date'])
        elif data_filter['user_id'] and not data_filter['start_date']:
            filename = 'Report_Request_Order_{0}_all.pdf'.format(data_filter['user_id'])
        else:
            filename = 'Report_Request_Order_{0}_{1}_{2}.pdf'.format(
                data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
            )
    else:
        filename = 'Report_Request_Order_all.pdf'

    response = make_response(result['file'])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/request/<request_id>', methods=['GET'])
@jwt_required()
def get_sales_request(request_id):
    """
    Get data Request Order
    :return:
    """
    user_id = current_identity.id
    username = current_identity.username

    tipe = 'mobile'

    if request.args.get('type'):
        tipe = 'web'

    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if tipe == 'web':
        request_order = sales_controller.get_request_order_by_id(request_id)
    else:
        request_order = sales_controller.get_all_sales_request_by_customer(
            customer=request_id, page=1, limit=1000, user_id=user_id, username=username
        )

    response['error'] = 0
    response['data'] = request_order
    return jsonify(response)


@bp.route('/sales/request/<request_id>/product', methods=['GET'])
@jwt_required()
def get_sales_request_product(request_id):
    """
    Get data Request Order
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    product = sales_controller.get_all_request_product_data(request_id)

    response['error'] = 0
    response['data'] = product
    return jsonify(response)


@bp.route('/sales/request/<request_id>/image', methods=['GET'])
@jwt_required()
def get_sales_request_image(request_id):
    """
    Get data Request Order
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    product = sales_controller.get_all_request_image_data(request_id)

    response['error'] = 0
    response['data'] = product
    return jsonify(response)


# TODO: ========================Section Sales Order===================
@bp.route('/sales/order', methods=['GET'])
@jwt_required()
def get_all_sales_order():
    """
    Get List Sales Order
    :return:
    """
    sales_controller = SalesController()

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

    sales_order = sales_controller.get_all_sales_order_data(
        page=page, limit=limit, search=search, column=column, direction=direction, branch_privilege=branch_privilege,
        division_privilege=division_privilege, data_filter=data_filter
    )

    response['error'] = 0
    response['data'] = sales_order

    return jsonify(response)


@bp.route('/sales/order/export', methods=['GET'])
@jwt_required()
def export_all_sales_order():
    """
    Get List Sales Order
    :return:
    """
    sales_controller = SalesController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 100000
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

    result = sales_controller.get_all_export_sales_order_data(
        page=page, limit=limit, search=search, column=column, direction=direction, branch_privilege=branch_privilege,
        division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date']:
            filename = 'Report_Sales_Order_{0}_{1}.xlsx'.format(data_filter['start_date'], data_filter['end_date'])
        else:
            filename = 'Report_Sales_Order_all.xlsx'
    else:
        filename = 'Report_Sales_Order_all.xlsx'

    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/order/export/pdf', methods=['GET'])
@jwt_required()
def export_pdf_all_sales_order():
    """
    Get List Sales Order
    :return:
    """
    sales_controller = SalesController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 100000
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

    result = sales_controller.get_all_export_pdf_sales_order_data(
        page=page, limit=limit, search=search, column=column, direction=direction, branch_privilege=branch_privilege,
        division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date']:
            filename = 'Report_Sales_Order_{0}_{1}.pdf'.format(data_filter['start_date'], data_filter['end_date'])
        else:
            filename = 'Report_Sales_Order_all.pdf'
    else:
        filename = 'Report_Sales_Order_all.pdf'

    response = make_response(result['file'])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/order/<order_id>', methods=['GET'])
@jwt_required()
def get_sales_order(order_id):
    """
    Get List Sales Order
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    sales_order = sales_controller.get_sales_order_by_id(order_id)

    response['error'] = 0
    response['data'] = sales_order
    return jsonify(response)


@bp.route('/sales/order/import', methods=['POST'])
@jwt_required()
def import_so_file():
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
    allowed_extensions = {'xls', 'xlsx'}

    user_id = current_identity.id
    sales_activities = current_identity.permissions['sales']['data']['sales-activities']['data'][
        'sales-activities-sales-order']
    permissions = sales_activities['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            sales_activities = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-sales-order']
            permissions = sales_activities['rule'][4]
        else:
            permissions = 0

    sales_controller = SalesController()
    table_name = 'sales_orders'
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
            result = sales_controller.import_so_file(filename=today+'_'+filename, filename_origin=filename,
                                                     table=table_name, user_id=user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    elif permissions == 2 or permissions == 3:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            # filename = secure_filename(import_file.filename)
            # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = sales_controller.import_so(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/sales/order/import', methods=['GET'])
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
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    import_list = sales_controller.get_all_sales_order_import()

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
    sales_controller = SalesController()
    user_id = current_identity.id
    sales_activities = current_identity.permissions['sales']['data']['sales-activities']['data'][
        'sales-activities-sales-order']
    permissions = sales_activities['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            sales_activities = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-sales-order']
            permissions = sales_activities['rule'][4]
        else:
            permissions = 0
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if permissions == 3:
        get_file = sales_controller.get_import_file(import_id, 'so')
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, filename)

        result = sales_controller.import_so(import_file, user_id)

        update_status = sales_controller.update_import_file(import_id, user_id, 'so')

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


# TODO: ========================Section Sales Invoice===================
@bp.route('/sales/invoice', methods=['GET'])
@jwt_required()
def get_all_sales_invoice():
    """
    Get List Sales Invoice
    :return:
    """
    sales_controller = SalesController()

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
    dropdown = False
    division = 0
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('dropdown'):
        division = request.args.get('division')
        dropdown = True
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    sales_order = sales_controller.get_all_sales_invoice_data(
        page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown, division=division,
        branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
    )

    response['error'] = 0
    response['data'] = sales_order

    return jsonify(response)


@bp.route('/sales/invoice/export', methods=['GET'])
@jwt_required()
def export_all_sales_invoice():
    """
    Get List Sales Invoice
    :return:
    """
    sales_controller = SalesController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    dropdown = False
    division = 0
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('dropdown'):
        division = request.args.get('division')
        dropdown = True
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = sales_controller.get_all_export_sales_invoice_data(
        page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown, division=division,
        branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date']:
            filename = 'Report_Invoice_{0}_{1}.xlsx'.format(data_filter['start_date'], data_filter['end_date'])
        else:
            filename = 'Report_Invoice_all.xlsx'
    else:
        filename = 'Report_Invoice_all.xlsx'

    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/invoice/export/pdf', methods=['GET'])
@jwt_required()
def export_pdf_all_sales_invoice():
    """
    Get List Sales Invoice
    :return:
    """
    sales_controller = SalesController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    page = 1
    limit = 100000
    search = None
    column = None
    direction = None
    dropdown = False
    division = 0
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('dropdown'):
        division = request.args.get('division')
        dropdown = True
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = sales_controller.get_all_export_pdf_sales_invoice_data(
        page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown, division=division,
        branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date']:
            filename = 'Report_Invoice_{0}_{1}.pdf'.format(data_filter['start_date'], data_filter['end_date'])
        else:
            filename = 'Report_Invoice_all.pdf'
    else:
        filename = 'Report_Invoice_all.pdf'

    response = make_response(result['file'])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/invoice/customer', methods=['GET'])
@jwt_required()
def get_all_sales_invoice_customer():
    """
    Get List Sales Invoice
    :return:
    """
    sales_controller = SalesController()

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
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('customer_code'):
        customer_code = request.args.get('customer_code')
        customer_code = customer_code.split(',')
    else:
        raise BadRequest("Params is missing for customer code", 422, 1, data=[])
    if request.args.get('division'):
        division = request.args.get('division')
    else:
        raise BadRequest("Params is missing for division id", 422, 1, data=[])

    sales_order = sales_controller.get_all_sales_invoice_data_by_customer(
        page=page, limit=limit, search=search, column=column, direction=direction, customer_code=customer_code,
        division=division
    )

    response['error'] = 0
    response['data'] = sales_order

    return jsonify(response)


@bp.route('/sales/invoice/<invoice_id>', methods=['GET'])
@jwt_required()
def get_sales_invoice(invoice_id):
    """
    Get Sales Invoice
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    invoice = sales_controller.get_sales_invoice_by_id(invoice_id)

    response['error'] = 0
    response['data'] = invoice
    return jsonify(response)


@bp.route('/sales/invoice/confirm', methods=["PUT"])
@jwt_required()
def confirm_invoice():
    """
    Confirm get invoice
    :example:

    :return:
    """
    sales_controller = SalesController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # update_data = request.get_json(silent=True)
    # list_id = update_data['invoice_id']
    # try:
    #     result = sales_controller.update_invoice(update_data, list_id)
    #     response['error'] = 0
    #     response['message'] = 'Success delete division'
    # except Exception as e:
    #     raise BadRequest(e, 500, 1, data=[])
    response = {
        'error': 0,
        'message': 'success confirm invoice',
        'data': []
    }
    return jsonify(response)


# TODO: ========================Section Sales Payment===================
@bp.route('/sales/payment', methods=["POST"])
@jwt_required()
def add_payment():
    """
    Create new payment
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "user_data:<json>"
        "http://localhost:7091/sales/request"
    :endpoint:
        POST /sales/request
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": 'Success create request order'
        }
    """
    user_id = current_identity.id
    sales_controller = SalesController()
    user_controller = UserController()
    inbox_controller = InboxController()
    setting_controller = SettingController()
    validator = Validator()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    # TODO: Get Json Data From FE
    try:
        request_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])
    print(request_data)
    rule = {}

    field_validator = validator.validator_field(request_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    result = sales_controller.create_payment_mobile(request_data, user_id)

    if result:
        response['error'] = 0
        response['message'] = 'Success create payment'
        payment = sales_controller.get_sales_payment_mobile_by_id(result)
        payment_amount = "Rp {:,}".format(payment['payment_amount'])
        notif_title = "Pembayaran"
        notif_body = "Pembayaran terhadap Customer Code: {0}, dengan code pembayaran: {1} dan jumlah sebesar: {2}".format(
            payment['customer_code'], payment['code'], payment_amount
        )
        notif_data = {
            'title': notif_title,
            'text': notif_body
        }
        try:
            list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
            device_ids = []
            if list_supervisor:
                list_supervisor.append(1)
                token = user_controller.get_device_token_by_list_id(list_supervisor)
                if token:
                    for rec in token:
                        device_ids.append(rec['token'])

                for rec in list_supervisor:
                    create_data = {
                        'title': notif_title,
                        'message': notif_body,
                        'category': 'activities',
                        'user_id': rec,
                        'from_id': payment['create_by'],
                        'payload': None
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass

                    message = None
                    # if user_controller.check_user_by_id(user_id):
                    for res in USERS_NOTIF:
                        if res['user_id'] == rec:
                            res['total'] += 1
                            message = res
                    if message:
                        pass
                    else:
                        USERS_NOTIF.append({
                            "user_id": rec,
                            "total": 1
                        })
                        message = {
                            "user_id": rec,
                            "total": 1
                        }

                    socketio.emit('notif-{}'.format(rec), [message], broadcast=True)

            fcm.notify_multiple_devices(
                registration_ids=device_ids,
                message_title=notif_title,
                message_body=notif_body,
                data_message=notif_data
            )
        except Exception as e:
            print(e)
            pass

        # TODO: Send Email Finance
        try:
            random_code = setting_controller.get_print_unique_code()
            if payment['invoice'] is not None:
                sales_rep = payment['user']['employee_name']
                payment_code = payment['code']
                payment_date = payment['payment_date']
                payment_data = payment['invoice']
                amount_total = payment['invoice_amount']
                amount_payment = payment['payment_amount']
                amount_diff = amount_total - amount_payment
                unique_code = random_code
                # str_amount_total = "Rp {:,}".format(amount_total)
                # str_amount_payment = "Rp {:,}".format(amount_payment)
                # str_amount_diff = "Rp {:,}".format(amount_diff)

                subject = "PAYMENT INVOICE {0}".format(payment['customer_code'])
                msg = Message(
                    subject,
                    recipients=[current_app.config['MAIL_FINANCE_RECIPIENTS']]
                )
                msg.html = render_template(
                    'email_template.html', sales_rep=sales_rep, payment_code=payment_code, payment_date=payment_date,
                    payment=payment_data, amount_total=amount_total, amount_payment=amount_payment,
                    amount_diff=amount_diff, unique_code=unique_code
                )
                mail.send(msg)
            else:
                print("Payment don't have detail payment info")
                pass
        except Exception as e:
            print(e)
            pass
    else:
        raise BadRequest('Failed create permission and alert', 500, 1, data=[])

    # response = {
    #     'error': 0,
    #     'message': 'Success create payment',
    #     'data': []
    # }

    return jsonify(response)


@bp.route('/sales/payment/<payment_id>/reprint', methods=['PUT'])
@jwt_required()
def update_reprint(payment_id):
    """
    Update Reprint
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    update_data = dict()
    # TODO: Get Json Data From FE
    try:
        # update_data_json = request.get_json(silent=True)
        update_data['id'] = payment_id
        update_data['receipt_printed'] = {
            "inc": 1
        }
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    result = sales_controller.update_payment_reprint(update_data, payment_id)

    response['error'] = 0
    response['message'] = 'Success update reprint'
    return jsonify(response)


@bp.route('/sales/payment/mobile/<payment_id>', methods=['PUT'])
@jwt_required()
def update_payment(payment_id):
    """
    Update Approve and confirm cancel
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = payment_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    result = sales_controller.update_payment_reprint(update_data, payment_id)

    response['error'] = 0
    response['message'] = 'Success update payment'
    return jsonify(response)


@bp.route('/sales/payment/mobile', methods=['GET'])
@jwt_required()
def get_all_sales_payment_mobile():
    """
    Get List Sales Payment from mobile
    :return:
    """
    sales_controller = SalesController()
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    tipe = 'mobile'
    if request.args.get('type'):
        tipe = 'web'
    data_filter = None
    if tipe == 'web':
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
        if request.args.get('page_filter'):
            data_filter = request.args.get('page_filter')
            data_filter = json.loads(data_filter)

        result = sales_controller.get_all_payment_mobile_data(
            page=page, limit=limit, search=search, column=column, direction=direction, tipe=tipe, visit_plan_id=None,
            customer=None, branch_privilege=branch_privilege, division_privilege=division_privilege,
            data_filter=data_filter
        )
    else:
        visit_plan_id = int(request.args.get('visit_plan_id'))
        customer = None
        if request.args.get('customer'):
            customer = request.args.get('customer')
        result = sales_controller.get_all_payment_mobile_data(
            page=1, limit=1000, search=None, column=None, direction=None, tipe=tipe, visit_plan_id=visit_plan_id,
            customer=customer, branch_privilege=branch_privilege, division_privilege=division_privilege,
            data_filter=data_filter
        )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/sales/payment/mobile/export', methods=['GET'])
@jwt_required()
def export_all_sales_payment_mobile():
    """
    Get List Sales Payment from mobile
    :return:
    """
    sales_controller = SalesController()
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    tipe = 'mobile'
    if request.args.get('type'):
        tipe = 'web'
    data_filter = None
    if tipe == 'web':
        page = 1
        limit = 100000
        search = None
        column = None
        direction = None
        if request.args.get('search'):
            search = request.args.get('search')
        if request.args.get('order_by_column'):
            column = request.args.get('order_by_column')
            direction = request.args.get('order_direction')
        if request.args.get('page_filter'):
            data_filter = request.args.get('page_filter')
            data_filter = json.loads(data_filter)

        result = sales_controller.get_all_export_payment_mobile_data(
            page=page, limit=limit, search=search, column=column, direction=direction, tipe=tipe, visit_plan_id=None,
            customer=None, branch_privilege=branch_privilege, division_privilege=division_privilege,
            data_filter=data_filter
        )
    else:
        visit_plan_id = int(request.args.get('visit_plan_id'))
        customer = None
        if request.args.get('customer'):
            customer = request.args.get('customer')
        result = sales_controller.get_all_export_payment_mobile_data(
            page=1, limit=1000, search=None, column=None, direction=None, tipe=tipe, visit_plan_id=visit_plan_id,
            customer=customer, branch_privilege=branch_privilege, division_privilege=division_privilege,
            data_filter=data_filter
        )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date'] and not data_filter['user_id']:
            filename = 'Report_Payment_all_{0}_{1}.xlsx'.format(data_filter['start_date'], data_filter['end_date'])
        elif data_filter['user_id'] and not data_filter['start_date']:
            filename = 'Report_Payment_{0}_all.xlsx'.format(data_filter['user_id'])
        else:
            filename = 'Report_Payment_{0}_{1}_{2}.xlsx'.format(
                data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
            )
    else:
        filename = 'Report_Payment_all.xlsx'

    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/payment/mobile/export/pdf', methods=['GET'])
@jwt_required()
def export_pdf_all_sales_payment_mobile():
    """
    Get List Sales Payment from mobile
    :return:
    """
    sales_controller = SalesController()
    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    tipe = 'mobile'
    if request.args.get('type'):
        tipe = 'web'
    data_filter = None
    if tipe == 'web':
        page = 1
        limit = 100000
        search = None
        column = None
        direction = None
        if request.args.get('search'):
            search = request.args.get('search')
        if request.args.get('order_by_column'):
            column = request.args.get('order_by_column')
            direction = request.args.get('order_direction')
        if request.args.get('page_filter'):
            data_filter = request.args.get('page_filter')
            data_filter = json.loads(data_filter)

        result = sales_controller.get_all_export_pdf_payment_mobile_data(
            page=page, limit=limit, search=search, column=column, direction=direction, tipe=tipe, visit_plan_id=None,
            customer=None, branch_privilege=branch_privilege, division_privilege=division_privilege,
            data_filter=data_filter
        )
    else:
        visit_plan_id = int(request.args.get('visit_plan_id'))
        customer = None
        if request.args.get('customer'):
            customer = request.args.get('customer')
        result = sales_controller.get_all_export_pdf_payment_mobile_data(
            page=1, limit=1000, search=None, column=None, direction=None, tipe=tipe, visit_plan_id=visit_plan_id,
            customer=customer, branch_privilege=branch_privilege, division_privilege=division_privilege,
            data_filter=data_filter
        )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date'] and not data_filter['user_id']:
            filename = 'Report_Payment_all_{0}_{1}.pdf'.format(data_filter['start_date'], data_filter['end_date'])
        elif data_filter['user_id'] and not data_filter['start_date']:
            filename = 'Report_Payment_{0}_all.pdf'.format(data_filter['user_id'])
        else:
            filename = 'Report_Payment_{0}_{1}_{2}.pdf'.format(
                data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
            )
    else:
        filename = 'Report_Payment_all.pdf'

    response = make_response(result['file'])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/sales/payment/mobile/<payment_id>', methods=['GET'])
@jwt_required()
def get_sales_payment_mobile(payment_id):
    """
    Get Sales Payment
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    result = sales_controller.get_sales_payment_mobile_by_id(payment_id)

    response['error'] = 0
    response['data'] = result
    return jsonify(response)


@bp.route('/sales/payment', methods=['GET'])
@jwt_required()
def get_all_sales_payment():
    """
    Get List Sales Payment
    :return:
    """
    sales_controller = SalesController()
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

    result = sales_controller.get_all_sales_payment_data(
        page=page, limit=limit, search=search, column=column, direction=direction
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/sales/payment/<payment_id>', methods=['GET'])
@jwt_required()
def get_sales_payment(payment_id):
    """
    Get Sales Payment
    :return:
    """
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    sales_payment = sales_controller.get_sales_payment_by_id(payment_id)

    response['error'] = 0
    response['data'] = sales_payment
    return jsonify(response)


@bp.route('/sales/payment/import', methods=['POST'])
@jwt_required()
def import_sp_file():
    """
    Sales Payment import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "files:<file>"
        "http://localhost:7091/sales/payment/import"
    :endpoint:
        POST /sales/payment/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Success import payment"
        }
    """
    allowed_extensions = {'xls', 'xlsx'}

    user_id = current_identity.id
    sales_activities = current_identity.permissions['sales']['data']['sales-activities']['data'][
        'sales-activities-payment']
    permissions = sales_activities['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            sales_activities = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-payment']
            permissions = sales_activities['rule'][4]
        else:
            permissions = 0

    sales_controller = SalesController()
    table_name = 'sales_payment'
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
            result = sales_controller.import_sp_file(filename=today+'_'+filename, filename_origin=filename,
                                                     table=table_name, user_id=user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    elif permissions == 2 or permissions == 3:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            # filename = secure_filename(import_file.filename)
            # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = sales_controller.import_sp(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/sales/payment/import', methods=['GET'])
@jwt_required()
def get_import_sp_file_list():
    """
    Sales Payment import excel
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
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    import_list = sales_controller.get_all_sales_payment_import()

    response['error'] = 0
    response['data'] = import_list

    return jsonify(response)


@bp.route('/sales/payment/import/<import_id>/approve', methods=['POST'])
@jwt_required()
def approve_payment_import(import_id):
    """
    Sales Payment import approve
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
    sales_controller = SalesController()
    user_id = current_identity.id
    sales_activities = current_identity.permissions['sales']['data']['sales-activities']['data'][
        'sales-activities-payment']
    permissions = sales_activities['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            sales_activities = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-payment']
            permissions = sales_activities['rule'][4]
        else:
            permissions = 0
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if permissions == 3:
        get_file = sales_controller.get_import_file(import_id, 'sp')
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, filename)

        result = sales_controller.import_sp(import_file, user_id)

        update_status = sales_controller.update_import_file(import_id, user_id, 'sp')

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)