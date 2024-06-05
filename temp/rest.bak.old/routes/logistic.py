import re
import os
import json
import pandas as pd

from flask import Blueprint, jsonify, request, current_app, make_response, send_file
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename
from datetime import datetime

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file, USERS_NOTIF
from rest.controllers import LogisticController, DeliveryController, UserController, InboxController
from rest.helpers import fcm, socketio

__author__ = 'junior'

bp = Blueprint(__name__, "logistic")


# TODO: ================ Section Packing Slip ============
@bp.route('/packing/slip', methods=['GET'])
@jwt_required()
def get_all_packing_slip():
    """
    Get List Packing Slip
    :return:
    """
    logistic_controller = LogisticController()
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
    division = 0
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if request.args.get('dropdown'):
        dropdown = True
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = logistic_controller.get_all_packing_slip_data(
        page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown,
        branch_privilege=branch_privilege, data_filter=data_filter
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/packing/slip/customer', methods=['GET'])
@jwt_required()
def get_all_packing_slip_customer():
    """
    Get List Packing Slip
    :return:
    """
    logistic_controller = LogisticController()
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
    if request.args.get('customer_code'):
        customer_code = request.args.get('customer_code')
        customer_code = customer_code.split(',')
    else:
        raise BadRequest("Params is missing for customer code", 422, 1, data=[])

    result = logistic_controller.get_all_packing_slip_data_by_customer(
        page=page, limit=limit, search=search, column=column, direction=direction, customer_code=customer_code,
        branch_privilege=branch_privilege
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/packing/slip/export', methods=['GET'])
@jwt_required()
def export_all_packing_slip():
    """
    Get List Packing Slip
    :return:
    """
    logistic_controller = LogisticController()
    branch_privilege = current_identity.branch_privilege

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
        division = request.args.get('dropdown')
        dropdown = True
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = logistic_controller.get_all_export_packing_slip_data(
        page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown,
        branch_privilege=branch_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date']:
            filename = 'Report_Packing_Slip_{0}_{1}.xlsx'.format(data_filter['start_date'], data_filter['end_date'])
        else:
            filename = 'Report_Packing_Slip_all.xlsx'
    else:
        filename = 'Report_Packing_Slip_all.xlsx'

    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/packing/slip/export/pdf', methods=['GET'])
@jwt_required()
def export_pdf_all_packing_slip():
    """
    Get List Packing Slip
    :return:
    """
    logistic_controller = LogisticController()
    branch_privilege = current_identity.branch_privilege

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
        division = request.args.get('dropdown')
        dropdown = True
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = logistic_controller.get_all_export_pdf_packing_slip_data(
        page=page, limit=limit, search=search, column=column, direction=direction, dropdown=dropdown,
        branch_privilege=branch_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date']:
            filename = 'Report_Packing_Slip_{0}_{1}.pdf'.format(data_filter['start_date'], data_filter['end_date'])
        else:
            filename = 'Report_Packing_Slip_all.pdf'
    else:
        filename = 'Report_Packing_Slip_all.pdf'

    response = make_response(result['file'])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/packing/slip/<slip_id>', methods=['GET'])
@jwt_required()
def get_packing_slip(slip_id):
    """
    Get List Sales Order
    :return:
    """
    logistic_controller = LogisticController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    result = logistic_controller.get_packing_slip_by_id(slip_id)

    response['error'] = 0
    response['data'] = result
    return jsonify(response)


@bp.route('/packing/slip/import', methods=['POST'])
@jwt_required()
def import_packing_slip_file():
    """
    Packing Slip import excel
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/area"
    :endpoint:
        POST /packing/slip/import
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "packing slip has been created"
        }
    """
    allowed_extensions = {'xls', 'xlsx'}

    user_id = current_identity.id
    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-packing-slip']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-packing-slip']
            permissions = setting['rule'][4]
        else:
            permissions = 0

    logistic_controller = LogisticController()
    table_name = 'packing_slip'
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
            result = logistic_controller.import_packing_slip_file(
                filename=today + '_' + filename, filename_origin=filename, table=table_name, user_id=user_id
            )

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    elif permissions == 2 or permissions == 3:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            # filename = secure_filename(import_file.filename)
            # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
            result = logistic_controller.import_packing_slip(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/packing/slip/import', methods=['GET'])
@jwt_required()
def get_import_file_packing_list():
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
    logistic_controller = LogisticController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    import_list = logistic_controller.get_all_packing_slip_import()

    response['error'] = 0
    response['data'] = import_list

    return jsonify(response)


@bp.route('/packing/slip/import/<import_id>/approve', methods=['POST'])
@jwt_required()
def approve_import_packing(import_id):
    """
    Packing Slip import excel
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
    logistic_controller = LogisticController()
    user_id = current_identity.id
    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-packing-slip']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-packing-slip']
            permissions = setting['rule'][4]
        else:
            permissions = 0
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if permissions == 3:
        get_file = logistic_controller.get_import_file(import_id, 'so')
        filename = get_file['file_name']
        table_name = get_file['table_name']
        import_file = os.path.join(current_app.config['UPLOAD_FOLDER'] + '/' + table_name, filename)

        result = logistic_controller.import_packing_slip(import_file, user_id)

        update_status = logistic_controller.update_import_file(import_id, user_id, 'packing_slip')

        response['error'] = 0
        response['message'] = 'Import Success'
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


# TODO: ================ Section Accept Packing ============
@bp.route('/packing/slip/<packing_id>/accept', methods=['POST'])
@jwt_required()
def accept_deliver_packing_slip(packing_id):
    """
    Accept delivery packing slip
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/packing/slip/<packing_id>/accept"
    :endpoint:
        POST /area
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "delivery confirm has been created"
        }
    """
    user_id = current_identity.id
    logistic_controller = LogisticController()
    delivery_controller = DeliveryController()
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
        raise BadRequest("Params is missing or error format, check double quatation", 422, 1, data=[])

    rule = {}

    field_validator = validator.validator_field(request_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    result = logistic_controller.accept_packing_slip(request_data, user_id, packing_id)

    if result:
        response['error'] = 0
        response['message'] = 'Success accept packing slip'
        delivery = delivery_controller.get_delivery_by_delivery_id(result)
        notif_title = "Pengiriman"
        notif_body = "Pengiriman terhadap Customer Code: {0}, dengan Packing Slip code: {1} Telah diterima".format(
            delivery['customer_code'], delivery['packing_slip_code']
        )
        notif_data = {
            'title': notif_title,
            'text': notif_body
        }
        try:
            list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
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
                        'from_id': delivery['user_id'],
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
        raise BadRequest('Failed accept packing slip', 500, 1, data=[])

    return jsonify(response)


@bp.route('/packing/slip/<packing_id>/reject', methods=['POST'])
@jwt_required()
def reject_deliver_packing_slip(packing_id):
    """
    Accept delivery packing slip
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "area_data:<json>"
        "http://localhost:7091/packing/slip/<packing_id>/accept"
    :endpoint:
        POST /area
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "delivery confirm has been created"
        }
    """
    user_id = current_identity.id
    logistic_controller = LogisticController()
    delivery_controller = DeliveryController()
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
        raise BadRequest("Params is missing or error format, check double quatation", 422, 1, data=[])

    rule = {}

    field_validator = validator.validator_field(request_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    result = logistic_controller.reject_packing_slip(request_data, user_id, packing_id)

    if result:
        response['error'] = 0
        response['message'] = 'Success reject packing slip'

        delivery = delivery_controller.get_delivery_by_delivery_id(result)
        notif_title = "Pengiriman"
        notif_body = "Pengiriman terhadap Customer Code: {0}, dengan Packing Slip code: {1} Telah ditolak".format(
            delivery['customer_code'], delivery['packing_slip_code']
        )
        notif_data = {
            'title': notif_title,
            'text': notif_body
        }
        try:
            list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
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
                        'from_id': delivery['user_id'],
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
        raise BadRequest('Failed reject packing slip', 500, 1, data=[])

    return jsonify(response)
