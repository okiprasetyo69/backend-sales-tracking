import os
import json

from flask import Blueprint, jsonify, request, current_app, make_response, send_file
from flask_jwt import jwt_required, current_identity

from rest.controllers import PermissionsController, UserController, InboxController, \
    SalesActivityController, LogisticActivityController, SalesController, CustomerController
from rest.exceptions import BadRequest
from rest.helpers import Validator, USERS_NOTIF
from rest.helpers import fcm, socketio

# from rest.sockets.notif import USERS_NOTIF

__author__ = 'junior'

bp = Blueprint(__name__, "permissions")


@bp.route('/permission_alert', methods=["POST"])
@jwt_required()
def add_permission_alert():
    """
    Create new permission and alert
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "user_data:<json>"
        "http://localhost:7091/permission_alert"
    :endpoint:
        POST /permission_alert
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Permission and alert has been created"
        }
    """
    user_id = current_identity.id
    permissions_controller = PermissionsController()
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

    result = permissions_controller.create(request_data, user_id)

    if result:
        response['error'] = 0
        response['message'] = 'Success create data permissions and alert'
        permission = permissions_controller.get_permission_alert_by_id(result)
        if permission['type'] == 'break_time':
            notif_title = "Permintaan Break Time"
            notif_body = "Permintaan break time pengguna {0} selama {1} menit".format(
                permission['create_user']['name'], int(permission['description']['time'])
            )
            notif_data = {
                'title': notif_title,
                'text': notif_body
            }
            try:
                if permission['visit_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
                elif permission['delivery_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
                else:
                    list_supervisor = None
                device_ids = []
                if list_supervisor:
                    list_supervisor.append(1)
                    token = user_controller.get_device_token_by_list_id(list_supervisor)
                    if token:
                        for rec in token:
                            device_ids.append(rec['token'])

                    for rec in list_supervisor:
                        print(rec)
                        create_data = {
                            'title': notif_title,
                            'message': notif_body,
                            'category': 'permission',
                            'user_id': rec,
                            'from_id': permission['create_by'],
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
        elif permission['type'] == 'visit_time':
            notif_title = "Permintaan Visit Time"
            notif_body = "Permintaan visit time pengguna {0} selama {1} menit".format(
                permission['create_user']['name'], int(permission['description']['time'])
            )
            notif_data = {
                'title': notif_title,
                'text': notif_body
            }
            try:
                if permission['visit_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
                elif permission['delivery_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
                else:
                    list_supervisor = None
                device_ids = []
                if list_supervisor:
                    list_supervisor.append(1)
                    token = user_controller.get_device_token_by_list_id(list_supervisor)
                    if token:
                        for rec in token:
                            device_ids.append(rec['token'])

                    for rec in list_supervisor:
                        print(rec)
                        create_data = {
                            'title': notif_title,
                            'message': notif_body,
                            'category': 'permission',
                            'user_id': rec,
                            'from_id': permission['create_by'],
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
        elif permission['type'] == 'routes':
            notif_title = "Permintaan Pergantian Route"
            notif_body = "Permintaan pergantian route sales {0}".format(
                permission['create_user']['name']
            )
            notif_data = {
                'title': notif_title,
                'text': notif_body
            }
            try:
                if permission['visit_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
                elif permission['delivery_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
                else:
                    list_supervisor = None
                device_ids = []
                if list_supervisor:
                    list_supervisor.append(1)
                    token = user_controller.get_device_token_by_list_id(list_supervisor)
                    if token:
                        for rec in token:
                            device_ids.append(rec['token'])

                    for rec in list_supervisor:
                        print(rec)
                        create_data = {
                            'title': notif_title,
                            'message': notif_body,
                            'category': 'permission',
                            'user_id': rec,
                            'from_id': permission['create_by'],
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
        elif permission['type'] == 'print':
            notif_title = "Permintaan Re-print bukti pembayaran"
            notif_body = "Permintaan Re-print bukti pembayaran"
            notif_data = {
                'title': notif_title,
                'text': notif_body
            }
            try:
                if permission['visit_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
                elif permission['delivery_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
                else:
                    list_supervisor = None
                device_ids = []
                if list_supervisor:
                    list_supervisor.append(1)
                    token = user_controller.get_device_token_by_list_id(list_supervisor)
                    if token:
                        for rec in token:
                            device_ids.append(rec['token'])

                    for rec in list_supervisor:
                        print(rec)
                        create_data = {
                            'title': notif_title,
                            'message': notif_body,
                            'category': 'print',
                            'user_id': rec,
                            'from_id': permission['create_by'],
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
        elif permission['type'] == 'report':
            if permission['description']['type'] == 'location':
                notif_title = "Laporan Location"
                notif_body = "{}".format(permission['notes'])
            elif permission['description']['type'] == 'nfc':
                notif_title = "Laporan NFC"
                notif_body = "{}".format(permission['notes'])
            elif permission['description']['type'] == 'closed':
                notif_title = "Laporan Toko Tutup"
                notif_body = "{}".format(permission['notes'])
            elif permission['description']['type'] == 'print':
                notif_title = "Laporan Print"
                notif_body = "{}".format(permission['notes'])
            else:
                notif_title = "Laporan Lainnya"
                notif_body = "{}".format(permission['notes'])
            notif_data = {
                'title': notif_title,
                'text': notif_body
            }
            try:
                if permission['visit_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
                elif permission['delivery_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
                else:
                    list_supervisor = None
                device_ids = []
                if list_supervisor:
                    list_supervisor.append(1)
                    token = user_controller.get_device_token_by_list_id(list_supervisor)
                    if token:
                        for rec in token:
                            device_ids.append(rec['token'])

                    for rec in list_supervisor:
                        print(rec)
                        create_data = {
                            'title': notif_title,
                            'message': notif_body,
                            'category': 'report',
                            'user_id': rec,
                            'from_id': permission['create_by'],
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
        elif permission['type'] == 'alert':
            notif_title = "Peringatan"
            notif_body = "Pengguna {0}: {1}".format(
                permission['create_user']['name'], permission['notes']
            )
            notif_data = {
                'title': notif_title,
                'text': notif_body
            }
            try:
                # token = user_controller.get_device_token_by_id(permission['create_by'])
                # device_id = token['token']
                # fcm.notify_single_device(
                #     registration_id=device_id,
                #     message_title=notif_title,
                #     message_body=notif_body,
                #     data_message=notif_data
                # )
                if permission['visit_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="sales")
                elif permission['delivery_plan_id'] is not None:
                    list_supervisor = user_controller.get_supervisor_by_id(user_id, category="logistic")
                else:
                    list_supervisor = None
                device_ids = []
                if list_supervisor:
                    list_supervisor.append(1)
                    token = user_controller.get_device_token_by_list_id(list_supervisor)
                    if token:
                        for rec in token:
                            device_ids.append(rec['token'])

                    for rec in list_supervisor:
                        print(rec)
                        create_data = {
                            'title': notif_title,
                            'message': notif_body,
                            'category': 'alert',
                            'user_id': rec,
                            'from_id': permission['create_by'],
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

    return jsonify(response)


@bp.route('/permission_alert', methods=["GET"])
@jwt_required()
def permission_alert_all_list():
    """
    list all Permissions and Alert
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/permission_alert?page=1&limit=50"
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

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    job_function = current_identity.job_function
    is_supervisor_sales = current_identity.is_supervisor_sales
    is_supervisor_logistic = current_identity.is_supervisor_logistic

    permissions_controller = PermissionsController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = int(request.args.get('page'))
    limit = int(request.args.get('limit'))
    tipe = None
    category = "all"
    log = False
    search = None
    column = None
    direction = None
    job_category = None
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('type'):
        tipe = request.args.get('type')
    if request.args.get('category'):
        category = request.args.get('category')
    if request.args.get('log'):
        log = request.args.get('log')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if job_function == 'supervisor':
        if is_supervisor_sales == 1 and is_supervisor_logistic == 0:
            job_category = 'sales'
        elif is_supervisor_sales == 0 and is_supervisor_logistic == 1:
            job_category = 'logistic'
        elif is_supervisor_sales == 1 and is_supervisor_logistic == 1:
            job_category = 'all'
        else:
            raise BadRequest(
                "Can't view list customer, only with assign supervisor sales or logistic", 422, 1, data=[]
            )
    if request.args.get('job_category'):
        job_category = request.args.get('job_category')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = permissions_controller.get_all_permission_alert_data(
        page=page, limit=limit, search=search, column=column, direction=direction, tipe=tipe,
        category=category, log=log, user_id=user_id, job_category=job_category, branch_privilege=branch_privilege,
        division_privilege=division_privilege, data_filter=data_filter
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/permission_alert/export', methods=["GET"])
@jwt_required()
def export_alert_all_list():
    """
    list all Permissions and Alert
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/permission_alert?page=1&limit=50"
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

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    job_function = current_identity.job_function
    is_supervisor_sales = current_identity.is_supervisor_sales
    is_supervisor_logistic = current_identity.is_supervisor_logistic

    permissions_controller = PermissionsController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    tipe = None
    category = "all"
    log = False
    search = None
    column = None
    direction = None
    job_category = None
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('type'):
        tipe = request.args.get('type')
    if request.args.get('category'):
        category = request.args.get('category')
    if request.args.get('log'):
        log = request.args.get('log')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if job_function == 'supervisor':
        if is_supervisor_sales == 1 and is_supervisor_logistic == 0:
            job_category = 'sales'
        elif is_supervisor_sales == 0 and is_supervisor_logistic == 1:
            job_category = 'logistic'
        elif is_supervisor_sales == 1 and is_supervisor_logistic == 1:
            job_category = 'all'
        else:
            raise BadRequest(
                "Can't view list customer, only with assign supervisor sales or logistic", 422, 1, data=[]
            )
    if request.args.get('job_category'):
        job_category = request.args.get('job_category')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = permissions_controller.get_all_export_permission_alert_data(
        page=page, limit=limit, search=search, column=column, direction=direction, tipe=tipe,
        category=category, log=log, user_id=user_id, job_category=job_category, branch_privilege=branch_privilege,
        division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date'] and not data_filter['user_id']:
            if category == 'permission':
                filename = 'Report_Permission_all_{0}_{1}.xlsx'.format(data_filter['start_date'], data_filter['end_date'])
            else:
                filename = 'Report_Alert_all_{0}_{1}.xlsx'.format(data_filter['start_date'], data_filter['end_date'])
        elif data_filter['user_id'] and not data_filter['start_date']:
            if category == 'permission':
                filename = 'Report_Permission_{0}_all.xlsx'.format(data_filter['user_id'])
            else:
                filename = 'Report_Alert_{0}_all.xlsx'.format(data_filter['user_id'])
        else:
            if category == 'permission':
                filename = 'Report_Permission_{0}_{1}_{2}.xlsx'.format(
                    data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
                )
            else:
                filename = 'Report_Alert_{0}_{1}_{2}.xlsx'.format(
                    data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
                )
    else:
        if category == 'permission':
            filename = 'Report_Permission_all.xlsx'
        else:
            filename = 'Report_Alert_all.xlsx'

    response = make_response(send_file(result['file'], add_etags=False))
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/permission_alert/export/pdf', methods=["GET"])
@jwt_required()
def export_pdf_alert_all_list():
    """
    list all Permissions and Alert
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/permission_alert?page=1&limit=50"
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

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    job_function = current_identity.job_function
    is_supervisor_sales = current_identity.is_supervisor_sales
    is_supervisor_logistic = current_identity.is_supervisor_logistic

    permissions_controller = PermissionsController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    page = 1
    limit = 100000
    tipe = None
    category = "all"
    log = False
    search = None
    column = None
    direction = None
    job_category = None
    data_filter = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('type'):
        tipe = request.args.get('type')
    if request.args.get('category'):
        category = request.args.get('category')
    if request.args.get('log'):
        log = request.args.get('log')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')
    if job_function == 'supervisor':
        if is_supervisor_sales == 1 and is_supervisor_logistic == 0:
            job_category = 'sales'
        elif is_supervisor_sales == 0 and is_supervisor_logistic == 1:
            job_category = 'logistic'
        elif is_supervisor_sales == 1 and is_supervisor_logistic == 1:
            job_category = 'all'
        else:
            raise BadRequest(
                "Can't view list customer, only with assign supervisor sales or logistic", 422, 1, data=[]
            )
    if request.args.get('job_category'):
        job_category = request.args.get('job_category')
    if request.args.get('page_filter'):
        data_filter = request.args.get('page_filter')
        data_filter = json.loads(data_filter)

    result = permissions_controller.get_all_export_pdf_permission_alert_data(
        page=page, limit=limit, search=search, column=column, direction=direction, tipe=tipe,
        category=category, log=log, user_id=user_id, job_category=job_category, branch_privilege=branch_privilege,
        division_privilege=division_privilege, data_filter=data_filter
    )

    if data_filter:
        data_filter = data_filter[0]
        if data_filter['start_date'] and not data_filter['user_id']:
            if category == 'permission':
                filename = 'Report_Permission_all_{0}_{1}.pdf'.format(data_filter['start_date'], data_filter['end_date'])
            else:
                filename = 'Report_Alert_all_{0}_{1}.pdf'.format(data_filter['start_date'], data_filter['end_date'])
        elif data_filter['user_id'] and not data_filter['start_date']:
            if category == 'permission':
                filename = 'Report_Permission_{0}_all.pdf'.format(data_filter['user_id'])
            else:
                filename = 'Report_Alert_{0}_all.pdf'.format(data_filter['user_id'])
        else:
            if category == 'permission':
                filename = 'Report_Permission_{0}_{1}_{2}.pdf'.format(
                    data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
                )
            else:
                filename = 'Report_Alert_{0}_{1}_{2}.pdf'.format(
                    data_filter['user_id'], data_filter['start_date'], data_filter['end_date']
                )
    else:
        if category == 'permission':
            filename = 'Report_Permission_all.pdf'
        else:
            filename = 'Report_Alert_all.pdf'

    response = make_response(result['file'])
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


@bp.route('/permission_alert/<id_permission>', methods=["GET"])
@jwt_required()
def permission_alert_data(id_permission):
    """
    Get data permission and alert tower by id
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        "http://localhost:7091/permission_alert/<id_permission>"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success"
            "data": Detail object
        }
    """
    permissions_controller = PermissionsController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    result = permissions_controller.get_permission_alert_by_id(id_permission)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/permission_alert/<id_permission>', methods=["PUT"])
@jwt_required()
def update_permission_alert_approve(id_permission):
    """
    Approve Edit division
    :example:
    :param id_permission:
    :param action:
    :return:

    """
    user_id = current_identity.id
    permissions_controller = PermissionsController()
    user_controller = UserController()
    inbox_controller = InboxController()
    sa_controller = SalesActivityController()
    lo_controller = LogisticActivityController()
    sales_controller = SalesController()
    customer_controller = CustomerController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = id_permission
        if update_data.get("is_approved"):
            update_data['approval_by'] = user_id
        if update_data.get("is_rejected"):
            update_data['reject_by'] = user_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

    permission = permissions_controller.get_permission_alert_by_id(id_permission)
    if permission:
        if permission['is_approved'] or permission['is_rejected']:
            raise BadRequest("validasi", 422, 1, data=['Permission has already been updated'])

    try:
        result = permissions_controller.update_permission_alert(update_data, user_id)

        response['error'] = 0
        if update_data.get("is_approved"):
            response['message'] = 'Success approve permission alert'
            permission = permissions_controller.get_permission_alert_by_id(id_permission)
            if permission['type'] == 'break_time':
                data_notif = {
                    "title": "Permintaan Break Time Diterima",
                    "text": "Permintaan break time yang diajukan telah diterima",
                    "type": "break_time",
                    "description": int(permission['description']['time']) * 60
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']

                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Break Time Diterima",
                        'message': "Permintaan break time yang diajukan telah diterima",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'visit_time':
                data_notif = {
                    "title": "Permintaan Visit Time Diterima",
                    "text": "Permintaan visit time yang diajukan telah diterima",
                    "type": "visit_time",
                    "description": int(permission['description']['time']) * 60
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Visit Time Diterima",
                        'message': "Permintaan visit time yang diajukan telah diterima",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'routes':
                data_notif = {
                    "title": "Permintaan Pergantian route Diterima",
                    "text": "Permintaan Pergantian route yang diajukan telah diterima",
                    "type": "routes",
                    "description": ''
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Pergantian route Diterima",
                        'message': "Permintaan Pergantian route yang diajukan telah diterima",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'print':
                data_notif = {
                    "title": "Permintaan Reprint",
                    "text": "Permintaan Reprint yang diajukan telah Diterima",
                    "type": "print"
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Reprint Diterima",
                        'message': "Permintaan reprint yang diajukan telah Diterima",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
                try:
                    update_data = dict()
                    update_data['id'] = permission['description']['payment_id']
                    update_data['receipt_reprint'] = {
                        "inc": 1
                    }
                    result = sales_controller.update_payment_reprint(update_data, permission['description']['payment_id'])
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'report':
                if permission['description']['type'] == 'nfc':
                    type_tap = "IN"
                    try:
                        if permission['delivery_plan_id'] is not None:
                            check_tap = lo_controller.check_tap_activity(
                                permission['delivery_plan_id'], permission['create_by'], permission['customer_code']
                            )
                            if check_tap:
                                type_tap = "OUT"
                            else:
                                type_tap = "IN"
                            if type_tap == "IN":
                                data_activity = {
                                    "delivery_plan_id": permission['delivery_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": permission['description']['distance'],
                                    "total_distance": None
                                }
                            else:
                                data_activity = {
                                    "delivery_plan_id": permission['delivery_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": None,
                                    "total_distance": None
                                }
                            try:
                                result = lo_controller.create(data_activity, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                        elif permission['visit_plan_id'] is not None:
                            check_tap = sa_controller.check_tap_activity(
                                permission['visit_plan_id'], permission['create_by'], permission['customer_code']
                            )
                            if check_tap:
                                type_tap = "OUT"
                            else:
                                type_tap = "IN"
                            if type_tap == "IN":
                                data_activity = {
                                    "visit_plan_id": permission['visit_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": permission['description']['distance'],
                                    "total_distance": None
                                }
                            else:
                                data_activity = {
                                    "visit_plan_id": permission['visit_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": None,
                                    "total_distance": None
                                }
                            try:
                                result = sa_controller.create(data_activity, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                    except Exception as e:
                        print(e)
                        pass
                    customer = customer_controller.get_customer_by_id(permission['customer_code'])
                    data_notif = {
                        "title": "Permintaan Laporan NFC",
                        "text": "Permintaan Laporan NFC yang diajukan telah diterima",
                        "type": "error_nfc",
                        "description": '',
                        "type_tap": type_tap,
                        "customer_code": permission['customer_code'],
                        "lat": customer['lat'],
                        "lng": customer['lng']
                    }
                elif permission['description']['type'] == 'location':
                    type_tap = "IN"
                    try:
                        if permission['delivery_plan_id'] is not None:
                            check_tap = lo_controller.check_tap_activity(
                                permission['delivery_plan_id'], permission['create_by'], permission['customer_code']
                            )
                            if check_tap:
                                type_tap = "OUT"
                            else:
                                type_tap = "IN"
                            if type_tap == "IN":
                                data_activity = {
                                    "delivery_plan_id": permission['delivery_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": permission['description']['distance'],
                                    "total_distance": None
                                }
                            else:
                                data_activity = {
                                    "delivery_plan_id": permission['delivery_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": None,
                                    "total_distance": None
                                }
                            try:
                                result = lo_controller.create(data_activity, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                        elif permission['visit_plan_id'] is not None:
                            check_tap = sa_controller.check_tap_activity(
                                permission['visit_plan_id'], permission['create_by'], permission['customer_code']
                            )
                            if check_tap:
                                type_tap = "OUT"
                            else:
                                type_tap = "IN"
                            if type_tap == "IN":
                                data_activity = {
                                    "visit_plan_id": permission['visit_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": permission['description']['distance'],
                                    "total_distance": None
                                }
                            else:
                                data_activity = {
                                    "visit_plan_id": permission['visit_plan_id'],
                                    "nfc_code": permission['customer_code'],
                                    "tap_nfc_type": type_tap,
                                    "route_breadcrumb": None,
                                    "distance": None,
                                    "total_distance": None
                                }
                            try:
                                result = sa_controller.create(data_activity, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                    except Exception as e:
                        print(e)
                        pass
                    customer = customer_controller.get_customer_by_id(permission['customer_code'])
                    data_notif = {
                        "title": "Permintaan Laporan Location",
                        "text": "Permintaan Laporan Location yang diajukan telah diterima",
                        "type": "error_nfc",
                        "description": '',
                        "type_tap": type_tap,
                        "customer_code": permission['customer_code'],
                        "lat": customer['lat'],
                        "lng": customer['lng']
                    }
                elif permission['description']['type'] == 'closed':
                    try:
                        if permission['delivery_plan_id'] is not None:
                            data_activity_in = {
                                "delivery_plan_id": permission['delivery_plan_id'],
                                "nfc_code": permission['customer_code'],
                                "tap_nfc_type": 'IN',
                                "route_breadcrumb": None,
                                "distance": permission['description']['distance'],
                                "total_distance": None
                            }
                            try:
                                result_in = lo_controller.create(data_activity_in, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                            data_activity_out = {
                                "delivery_plan_id": permission['delivery_plan_id'],
                                "nfc_code": permission['customer_code'],
                                "tap_nfc_type": 'OUT',
                                "route_breadcrumb": None,
                                "distance": None,
                                "total_distance": None
                            }
                            try:
                                result_out = lo_controller.create(data_activity_out, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                        elif permission['visit_plan_id'] is not None:
                            data_activity_in = {
                                "visit_plan_id": permission['visit_plan_id'],
                                "nfc_code": permission['customer_code'],
                                "tap_nfc_type": 'IN',
                                "route_breadcrumb": None,
                                "distance": permission['description']['distance'],
                                "total_distance": None
                            }
                            try:
                                result_in = sa_controller.create(data_activity_in, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                            data_activity_out = {
                                "visit_plan_id": permission['visit_plan_id'],
                                "nfc_code": permission['customer_code'],
                                "tap_nfc_type": 'OUT',
                                "route_breadcrumb": None,
                                "distance": None,
                                "total_distance": None
                            }
                            try:
                                result_out = sa_controller.create(data_activity_out, permission['create_by'])
                            except Exception as e:
                                print(e)
                                pass
                    except Exception as e:
                        print(e)
                        pass
                    customer = customer_controller.get_customer_by_id(permission['customer_code'])
                    data_notif = {
                        "title": "Permintaan Laporan Toko Tutup",
                        "text": "Permintaan Laporan Toko Tutup yang diajukan telah diterima",
                        "type": "closed",
                        "description": '',
                        "customer_code": permission['customer_code'],
                        "lat": customer['lat'],
                        "lng": customer['lng']
                    }
                elif permission['description']['type'] == 'print':
                    # data_notif = {
                    #     "title": "Permintaan Laporan Print",
                    #     "text": "Permintaan Laporan Print yang diajukan telah diterima",
                    #     "type": "error_print",
                    #     "description": '',
                    #     "customer_code": permission['customer_code']
                    # }
                    data_notif = {
                        "title": "Permintaan Laporan Print",
                        "text": "Permintaan Laporan Print yang diajukan telah diterima",
                        "type": "error_print",
                        "description": ''
                    }
                else:
                    data_notif = {
                        "title": "Permintaan Laporan Lainnya",
                        "text": "Permintaan Laporan Lainnya yang diajukan telah diterima",
                        "type": "error_other",
                        "description": ''
                    }

                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )

                    if permission['description']['type'] == 'nfc':
                        create_data = {
                            'title': "Permintaan Laporan NFC Diterima",
                            'message': "Permintaan Laporan NFC yang diajukan telah diterima",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    elif permission['description']['type'] == 'location':
                        create_data = {
                            'title': "Permintaan Laporan Location Diterima",
                            'message': "Permintaan Laporan Location yang diajukan telah diterima",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    elif permission['description']['type'] == 'closed':
                        create_data = {
                            'title': "Permintaan Laporan Toko Tutup Diterima",
                            'message': "Permintaan Laporan Toko Tutup yang diajukan telah diterima",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    elif permission['description']['type'] == 'print':
                        create_data = {
                            'title': "Permintaan Laporan Print Diterima",
                            'message': "Permintaan Laporan Print yang diajukan telah diterima",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    else:
                        create_data = {
                            'title': "Permintaan Laporan Lainnya Diterima",
                            'message': "Permintaan Laporan Lainnya yang diajukan telah diterima",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
        elif update_data.get("is_rejected"):
            response['message'] = 'Permission alert has been rejected'
            permission = permissions_controller.get_permission_alert_by_id(id_permission)
            if permission['type'] == 'break_time':
                data_notif = {
                    "title": "Permintaan Break Time Ditolak",
                    "text": "Permintaan break time yang diajukan telah Ditolak",
                    "type": "break_time"
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']

                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Break Time Ditolak",
                        'message': "Permintaan break time yang diajukan telah Ditolak",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'visit_time':
                data_notif = {
                    "title": "Permintaan Visit Time Ditolak",
                    "text": "Permintaan visit time yang diajukan telah Ditolak",
                    "type": "visit_time"
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Visit Time Ditolak",
                        'message': "Permintaan visit time yang diajukan telah Ditolak",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'print':
                data_notif = {
                    "title": "Permintaan Reprint Ditolak",
                    "text": "Permintaan Reprint yang diajukan telah Ditolak",
                    "type": "print"
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Reprint Ditolak",
                        'message': "Permintaan reprint yang diajukan telah Ditolak",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'routes':
                data_notif = {
                    "title": "Permintaan Pergantian route Ditolak",
                    "text": "Permintaan Pergantian route yang diajukan telah Ditolak",
                    "type": "routes",
                    "description": ''
                }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )
                    create_data = {
                        'title': "Permintaan Pergantian route Ditolak",
                        'message': "Permintaan Pergantian route yang diajukan telah Ditolak",
                        'category': 'permission',
                        'user_id': permission['create_by'],
                        'from_id': user_id,
                        'payload': json.dumps(permission['description'])
                    }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
            elif permission['type'] == 'report':
                if permission['description']['type'] == 'nfc':
                    data_notif = {
                        "title": "Permintaan Laporan NFC Ditolak",
                        "text": "Permintaan Laporan NFC yang diajukan telah Ditolak",
                        "description": ''
                    }
                elif permission['description']['type'] == 'closed':
                    data_notif = {
                        "title": "Permintaan Laporan Toko Tutup Ditolak",
                        "text": "Permintaan Laporan Toko Tutup yang diajukan telah Ditolak",
                        "description": ''
                    }
                elif permission['description']['type'] == 'print':
                    data_notif = {
                        "title": "Permintaan Laporan Print Ditolak",
                        "text": "Permintaan Laporan Print yang diajukan telah Ditolak",
                        "description": ''
                    }
                else:
                    data_notif = {
                        "title": "Permintaan Laporan Lainnya Ditolak",
                        "text": "Permintaan Laporan Lainnya yang diajukan telah Ditolak",
                        "description": ''
                    }
                try:
                    token = user_controller.get_device_token_by_id(permission['create_by'])
                    device_id = token['token']
                    fcm.notify_single_device(
                        registration_id=device_id,
                        data_message=data_notif
                    )

                    if permission['description']['type'] == 'nfc':
                        create_data = {
                            'title': "Permintaan Laporan NFC Ditolak",
                            'message': "Permintaan Laporan NFC yang diajukan telah Ditolak",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    elif permission['description']['type'] == 'closed':
                        create_data = {
                            'title': "Permintaan Laporan Toko Tutup Ditolak",
                            'message': "Permintaan Laporan Toko Tutup yang diajukan telah Ditolak",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    elif permission['description']['type'] == 'print':
                        create_data = {
                            'title': "Permintaan Laporan Print Ditolak",
                            'message': "Permintaan Laporan Print yang diajukan telah Ditolak",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    else:
                        create_data = {
                            'title': "Permintaan Laporan Lainnya Ditolak",
                            'message': "Permintaan Laporan Lainnya yang diajukan telah Ditolak",
                            'category': 'report',
                            'user_id': permission['create_by'],
                            'from_id': user_id,
                            'payload': data_notif
                        }
                    try:
                        result = inbox_controller.create(create_data)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    print(e)
                    pass
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)

