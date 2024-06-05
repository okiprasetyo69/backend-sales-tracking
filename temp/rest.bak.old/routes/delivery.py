import re
import json
import requests

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename
from datetime import datetime

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import DeliveryController, BranchesController, CustomerController, SalesController, \
    ApprovalController, LogisticActivityController

__author__ = 'junior'

bp = Blueprint(__name__, "delivery")


# TODO: routes for Delivery Cycle
# TODO: routes for Visit Cycle
@bp.route('/delivery/cycle/import', methods=['POST'])
@jwt_required()
def import_delivery_cycle_file():
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
    setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-delivery-cycle']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permissions = setting['rule'][4]
        else:
            permissions = 0

    delivery_controller = DeliveryController()
    # table_name = 'delivery'
    today = datetime.today()
    today = today.strftime("%Y%m%d")

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    import_file = request.files['files']

    # if permissions == 1:
    #     if import_file and allowed_file(import_file.filename, allowed_extensions):
    #         filename = secure_filename(import_file.filename)
    #         import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
    #         result = branch_controller.import_branch_file(filename=today+'_'+filename, filename_origin=filename,
    #                                                  table=table_name, user_id=user_id)
    #
    #         response['error'] = 0
    #         response['message'] = 'Import Success'
    #     else:
    #         raise BadRequest('Extension not allowed', 422, 1, data=[])
    # elif permissions == 2 or permissions == 3:
    #     if import_file and allowed_file(import_file.filename, allowed_extensions):
    #         # filename = secure_filename(import_file.filename)
    #         # import_file.save(os.path.join(current_app.config['UPLOAD_FOLDER']+'/'+table_name, today+'_'+filename))
    #         result = branch_controller.import_branch(import_file, user_id)
    #
    #         response['error'] = 0
    #         response['message'] = 'Import Success'
    #     else:
    #         raise BadRequest('Extension not allowed', 422, 1, data=[])
    # else:
    #     raise BadRequest("You don't have permission", 403, 1, data=[])
    if permissions != 0:
        if import_file and allowed_file(import_file.filename, allowed_extensions):
            result = delivery_controller.import_delivery_cycle(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/delivery/cycle', methods=['POST'])
@jwt_required()
def create_delivery_cycle():
    """
    Create new delivery cycle
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "cycle_data:<json>"
        "http://localhost:7091/visit/cycle"
    :endpoint:
        POST /delivery/cycle
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Visit cycle has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()

    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-delivery-cycle']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
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
        "user_id": {
            "required": True
        },
        "cycle_number": {
            "numeric": True,
            "required": True,
            "min": 1
        }
    }

    field_validator = validator.validator_field(request_data, rule)

    list_day = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for day in list_day:
        field = 'cycle_{}'.format(day)
        if request_data[field]:
            # if (request_data[field]['start_route_branch_id'] or request_data[field]['end_route_branch_id'] or request_data[field]['destination']):
            if (request_data[field]['start_route_branch_id'] or request_data[field]['end_route_branch_id']):
                if not request_data[field]['start_route_branch_id']:
                    field_validator.append({
                        "field": "cycle_{0}.start_route_branch_id".format(day),
                        "message": "Start route can't be empty"})
                elif not request_data[field]['end_route_branch_id']:
                    field_validator.append({
                        "field": "cycle_{0}.end_route_branch_id".format(day),
                        "message": "End route can't be empty"})

                # validation is_use_route
                if request_data[field]['is_use_route'] == 1:
                    if not request_data[field]['destination']:
                        field_validator.append({
                            "field": "cycle_{0}.destination".format(day),
                            "message": "Destination {0} can't be empty".format(field)})
                    else:
                        if not request_data[field]['destination_order']:
                            field_validator.append({
                                "field": "cycle_{0}.destination".format(day),
                                "message": "Please generate route for {0}".format(field)})
                else:
                    if not request_data[field]['route']:
                        if request_data[field]['destination']:
                            if not request_data[field]['destination_order']:
                                field_validator.append({
                                    "field": "cycle_{0}.route".format(day),
                                    "message": "Please Draw Pin Point for {0}".format(field)})

                # validation is_use_route
                # if request_data[field]['is_use_route'] == 1:
                #     if not request_data[field]['destination']:
                #         field_validator.append({
                #             "field": "cycle_{0}.destination".format(day),
                #             "message": "Destination {0} can't be empty".format(field)})
                #
                # # validation route for both use_route or not use_route (not only when is_use_route=1)
                # if not request_data[field]['route']:
                #     if not request_data[field]['destination_order']:
                #         if request_data[field]['is_use_route'] == 1:
                #             message = "Please generate route for {0}".format(field)
                #         else:
                #             message = "Please Draw Pin Point for {0}".format(field)
                #         field_validator.append({
                #             "field": "cycle_{0}.route".format(day),
                #             "message": message})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    id_user = request_data['user_id']
    cycle_no = request_data['cycle_number']
    if delivery_controller.check_delivery_cycle_by_user_cycle(id_user, cycle_no, None):
        field_validator.append({"field": "user_id", "message": "User is already used in cycle number"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    delivery_cycle = delivery_controller.create(request_data, user_id)

    if delivery_cycle:
        response['error'] = 0
        response['message'] = 'Success create delivery cycle'
        if permission == 1:
            result = delivery_controller.get_delivery_cycle_by_id(delivery_cycle)
            create_data = {
                "prefix": "delivery/cycle",
                "data_id": delivery_cycle,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "user_id": result['user_id'],
                    "asset_id": result['asset_id'],
                    "cycle_number": result['cycle_number'],
                    "cycle_monday": result['cycle_monday'],
                    "cycle_tuesday": result['cycle_tuesday'],
                    "cycle_wednesday": result['cycle_wednesday'],
                    "cycle_thursday": result['cycle_thursday'],
                    "cycle_friday": result['cycle_friday'],
                    "cycle_saturday": result['cycle_saturday'],
                    "cycle_sunday": result['cycle_sunday']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
                result = delivery_controller.rollback_cycle_insert(delivery_cycle)
                raise BadRequest('Failed create delivery cycle', 500, 1, data=[])
    else:
        raise BadRequest('Failed create delivery cycle', 500, 1, data=[])

    return jsonify(response)


@bp.route('/delivery/cycle', methods=["GET"])
@jwt_required()
def get_all_delivery_cycle():
    """
    Get List all Delivery Cycle
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

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
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')

    result = delivery_controller.get_all_delivery_cycle_data(
        page=page, limit=limit, search=search, column=column, direction=direction, branch_privilege=branch_privilege
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/delivery/cycle/approval', methods=["GET"])
@jwt_required()
def get_all_delivery_cycle_approval():
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

    branch_privilege = current_identity.branch_privilege

    setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-delivery-cycle']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
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

    result = approval_controller.get_all_approval_data_privilege(
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='delivery/cycle',
        permission=permission, branch_privilege=branch_privilege, division_privilege=None
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/delivery/cycle/<cycle_id>', methods=["GET"])
@jwt_required()
def get_delivery_cycle_by_id(cycle_id):
    """
    Get Delivery Cycle Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    delivery_controller = DeliveryController()
    result = delivery_controller.get_delivery_cycle_by_id(cycle_id)

    response['error'] = 0
    response['data'] = result
    return jsonify(response)


@bp.route('/delivery/cycle/<cycle_id>', methods=["PUT"])
@jwt_required()
def update_delivery_cycle(cycle_id):
    """
    Update Visit Cycle Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    validator = Validator()
    setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-delivery-cycle']
    permissions = setting['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permissions = setting['rule'][2]
        else:
            permissions = 0

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = cycle_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "user_id": {
            "required": True
        },
        "cycle_number": {
            "numeric": True,
            "required": True
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    list_day = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    for day in list_day:
        field = 'cycle_{}'.format(day)
        if update_data[field]:
            if (update_data[field]['start_route_branch_id'] or update_data[field]['end_route_branch_id']):
                if not update_data[field]['start_route_branch_id']:
                    field_validator.append({
                        "field": "cycle_{0}.start_route_branch_id".format(day),
                        "message": "Start route can't be empty"})
                if not update_data[field]['end_route_branch_id']:
                    field_validator.append({
                        "field": "cycle_{0}.end_route_branch_id".format(day),
                        "message": "End route can't be empty"})

                # validation is_use_route
                if update_data[field]['is_use_route'] == 1:
                    if not update_data[field]['destination']:
                        field_validator.append({
                            "field": "cycle_{0}.destination".format(day),
                            "message": "Destination {0} can't be empty".format(field)})
                    else:
                        if not update_data[field]['destination_order']:
                            field_validator.append({
                                "field": "cycle_{0}.destination".format(day),
                                "message": "Please generate route for {0}".format(field)})
                else:
                    if not update_data[field]['route']:
                        if update_data[field]['destination']:
                            if not update_data[field]['destination_order']:
                                field_validator.append({
                                    "field": "cycle_{0}.route".format(day),
                                    "message": "Please Draw Pin Point for {0}".format(field)})
            # # validation is_use_route
            # if update_data[field]['is_use_route'] == 1:
            #     if not update_data[field]['destination']:
            #         field_validator.append({
            #             "field": "cycle_{0}.destination".format(day),
            #             "message": "Destination {0} can't be empty".format(field)})
            #     if not update_data[field]['route']:
            #         field_validator.append({
            #             "field": "cycle_{0}.route".format(day),
            #             "message": "Please generate route for {0}".format(field)})

            # # clear destination and destination_order
            # if update_data[field]['is_use_route'] == 0:
            #     update_data[field]['route'] = None
            #     update_data[field]['destination_order'] = None

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    id_user = update_data['user_id']
    cycle_no = update_data['cycle_number']

    if delivery_controller.check_delivery_cycle_by_user_cycle(id_user, cycle_no, cycle_id):
        field_validator.append({"field": "user_id", "message": "User is already use in cycle number"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    del update_data['create_date'], update_data['update_date']

    if permissions == 1:
        edit_data = {
            "id": cycle_id,
            "edit_data": json.dumps(update_data)
        }
        try:
            delivery_cycle = delivery_controller.update_delivery_cycle(edit_data, cycle_id)

            response['error'] = 0
            response['message'] = 'Success request update delivery cycle'
            result = update_data
            create_data = {
                "prefix": "delivery/cycle",
                "data_id": cycle_id,
                "type": "edit",
                "data": {
                    "id": cycle_id,
                    "user_id": result['user_id'],
                    "asset_id": result['asset_id'],
                    "cycle_number": result['cycle_number'],
                    "cycle_monday": result['cycle_monday'],
                    "cycle_tuesday": result['cycle_tuesday'],
                    "cycle_wednesday": result['cycle_wednesday'],
                    "cycle_thursday": result['cycle_thursday'],
                    "cycle_friday": result['cycle_friday'],
                    "cycle_saturday": result['cycle_saturday'],
                    "cycle_sunday": result['cycle_sunday']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    elif permissions == 2 or permissions == 3:
        try:
            if update_data['cycle_monday'] is not None:
                update_data['cycle_monday'] = json.dumps(update_data['cycle_monday'])
            if update_data['cycle_tuesday'] is not None:
                update_data['cycle_tuesday'] = json.dumps(update_data['cycle_tuesday'])
            if update_data['cycle_wednesday'] is not None:
                update_data['cycle_wednesday'] = json.dumps(update_data['cycle_wednesday'])
            if update_data['cycle_thursday'] is not None:
                update_data['cycle_thursday'] = json.dumps(update_data['cycle_thursday'])
            if update_data['cycle_friday'] is not None:
                update_data['cycle_friday'] = json.dumps(update_data['cycle_friday'])
            if update_data['cycle_saturday'] is not None:
                update_data['cycle_saturday'] = json.dumps(update_data['cycle_saturday'])
            if update_data['cycle_sunday'] is not None:
                update_data['cycle_sunday'] = json.dumps(update_data['cycle_sunday'])

            delivery_cycle = delivery_controller.update_delivery_cycle(update_data, cycle_id)

            response['error'] = 0
            response['message'] = 'Success update delivery cycle'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/delivery/cycle/<cycle_id>/approve', methods=["PUT"])
@jwt_required()
def update_delivery_cycle_approve(cycle_id):
    """
    Approve `Create, Edit, Delete` Visit Cycle
    :example:
    :param cycle_id:
    :return:

    """
    user_id = current_identity.id
    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-delivery-cycle']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
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
                "id": cycle_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                delivery_cycle = delivery_controller.update_delivery_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success approve create delivery cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            delivery_cycle = delivery_controller.get_delivery_cycle_by_id(cycle_id)
            edit_data = delivery_cycle['edit_data']
            if edit_data['cycle_monday'] is not None:
                edit_data['cycle_monday'] = json.dumps(edit_data['cycle_monday'])
            if edit_data['cycle_tuesday'] is not None:
                edit_data['cycle_tuesday'] = json.dumps(edit_data['cycle_tuesday'])
            if edit_data['cycle_wednesday'] is not None:
                edit_data['cycle_wednesday'] = json.dumps(edit_data['cycle_wednesday'])
            if edit_data['cycle_thursday'] is not None:
                edit_data['cycle_thursday'] = json.dumps(edit_data['cycle_thursday'])
            if edit_data['cycle_friday'] is not None:
                edit_data['cycle_friday'] = json.dumps(edit_data['cycle_friday'])
            if edit_data['cycle_saturday'] is not None:
                edit_data['cycle_saturday'] = json.dumps(edit_data['cycle_saturday'])
            if edit_data['cycle_sunday'] is not None:
                edit_data['cycle_sunday'] = json.dumps(edit_data['cycle_sunday'])
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                delivery_cycle = delivery_controller.update_delivery_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success approve edit delivery cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = delivery_controller.get_delivery_cycle_by_id(cycle_id)
            count_delete = delivery_controller.get_delivery_cycle_delete_count(
                result['user_id'], result['cycle_number']
            )
            if count_delete:
                count_delete += 1
                update_data = {
                    "id": cycle_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                update_data = {
                    "id": cycle_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                result = delivery_controller.update_delivery_cycle(update_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success approve delete delivery cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            cycle_id, type_approve['type_approve'], "delivery/cycle"
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


@bp.route('/delivery/cycle/<cycle_id>/reject', methods=["PUT"])
@jwt_required()
def update_delivery_cycle_reject(cycle_id):
    """
    Approve `Create, Edit, Delete` Visit Cycle
    :example:
    :param cycle_id:
    :return:

    """
    user_id = current_identity.id
    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-delivery-cycle']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
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
            result = delivery_controller.get_delivery_cycle_by_id(cycle_id)
            count_delete = delivery_controller.get_delivery_cycle_delete_count(
                result['user_id'], result['cycle_number']
            )
            if count_delete:
                count_delete += 1
                edit_data = {
                    "id": cycle_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                edit_data = {
                    "id": cycle_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                delivery_cycle = delivery_controller.update_delivery_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success reject create delivery cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": cycle_id,
                "edit_data": None
            }
            try:
                delivery_cycle = delivery_controller.update_delivery_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success reject edit delivery cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": cycle_id,
                "is_delete_approval": False
            }
            try:
                result = delivery_controller.update_delivery_cycle(update_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success reject delete delivery cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            cycle_id, type_approve['type_approve'], "delivery/cycle"
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


@bp.route('/delivery/cycle/<cycle_id>', methods=["DELETE"])
@jwt_required()
def delete_delivery_cycle(cycle_id):
    """
    Delete delivery cycle
    :example:

    :param cycle_id:
    :return:
    """
    user_id = current_identity.id

    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['logistic']['data']['logistic-data']['data']['logistic-data-delivery-cycle']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-data']['data'][
                'logistic-data-delivery-cycle']
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
            "id": cycle_id,
            "is_delete_approval": True,
        }
        try:
            cycle = delivery_controller.update_delivery_cycle(update_data, cycle_id)
            response['error'] = 0
            response['message'] = 'Success request delete delivery cycle'

            result = delivery_controller.get_delivery_cycle_by_id(cycle_id)
            create_data = {
                "prefix": "delivery/cycle",
                "data_id": cycle_id,
                "type": "delete",
                "data": {
                    "id": cycle_id,
                    "user_id": result['user_id'],
                    "asset_id": result['asset_id'],
                    "cycle_number": result['cycle_number'],
                    "cycle_monday": result['cycle_monday'],
                    "cycle_tuesday": result['cycle_tuesday'],
                    "cycle_wednesday": result['cycle_wednesday'],
                    "cycle_thursday": result['cycle_thursday'],
                    "cycle_friday": result['cycle_friday'],
                    "cycle_saturday": result['cycle_saturday'],
                    "cycle_sunday": result['cycle_sunday']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = delivery_controller.get_delivery_cycle_by_id(cycle_id)
        count_delete = delivery_controller.get_delivery_cycle_delete_count(result['user_id'], result['cycle_number'])
        if count_delete:
            count_delete += 1
            update_data = {
                "id": cycle_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "id": cycle_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            cycle = delivery_controller.update_delivery_cycle(update_data, cycle_id)
            response['error'] = 0
            response['message'] = 'Success delete delivery cycle'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])
    return jsonify(response)


# TODO: Route for delivery plan
@bp.route('/delivery/plan/generate', methods=['POST'])
@jwt_required()
def generate_delivery_plan():
    """
    Generate visit plan from visit cycle
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "plan_data:<json>"
        "http://localhost:7091/visit/plan/generate"
    :endpoint:
        POST /visit/plan/generate
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Visit plan has been generate"
        }
    """
    user_id = current_identity.id
    validator = Validator()
    delivery_controller = DeliveryController()
    # setting = current_identity.permissions['sales']['data']['sales-activities']['data']['sales-activities-visit-plan']
    # permissions = setting['rule'][1]
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        request_data = request.get_json(silent=True)
        request_data['is_approval'] = True
        request_data['approval_by'] = user_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 422, 1, data=[])

    rule = {
        "user_id": {
            "required": True
        }
    }

    field_validator = validator.validator_field(request_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    id_user = request_data['user_id']
    result = delivery_controller.generate(request_data, id_user)

    if result:
        response['error'] = 0
        response['message'] = 'Success generate delivery plan'
    else:
        raise BadRequest('Failed generate delivery plan', 500, 1, data=[])

    return jsonify(response)


@bp.route('/delivery/plan', methods=['POST'])
@jwt_required()
def create_delivery_plan():
    """
    Create new delivery plan
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "cycle_data:<json>"
        "http://localhost:7091/visit/cycle"
    :endpoint:
        POST /visit/plan
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Visit plan has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()

    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-delivery-route']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
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
        "user_id": {
            "required": True
        },
        "date": {
            "required": True
        }
    }

    field_validator = validator.validator_field(request_data, rule)

    id_user = request_data['user_id']
    date = request_data['date']
    # if delivery_controller.check_delivery_plan(id_user, date, None):
    #     field_validator.append({"field": "user_id", "message": "User is already use in this date"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    delivery_plan = delivery_controller.create_delivery_plan(request_data, user_id)

    if delivery_plan:
        response['error'] = 0
        response['message'] = 'Success create delivery plan'
        if permission == 1:
            result = delivery_controller.get_delivery_plan_by_id(delivery_plan)
            create_data = {
                "prefix": "delivery/plan",
                "data_id": delivery_plan,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "user_id": result['user_id'],
                    "asset_id": result['asset_id'],
                    "date": result['date'],
                    "route": result['route'],
                    "destination": result['destination'],
                    "start_route_branch_id": result['start_route_branch_id'],
                    "end_route_branch_id": result['end_route_branch_id'],
                    "packing_slip_id": result['packing_slip_id']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
                result = delivery_controller.rollback_plan_insert(delivery_plan)
                raise BadRequest('Failed create delivery plan', 500, 1, data=[])
    else:
        raise BadRequest('Failed create delivery plan', 500, 1, data=[])

    return jsonify(response)


@bp.route('/delivery/plan/<plan_id>', methods=["PUT"])
@jwt_required()
def update_delivery_plan(plan_id):
    """
    Update Delivery Plan Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    validator = Validator()
    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-delivery-route']
    permissions = setting['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
            permissions = setting['rule'][2]
        else:
            permissions = 0

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
        update_data['id'] = plan_id
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

    rule = {
        "user_id": {
            "required": True
        },
        "date": {
            "required": True
        }
    }
    field_validator = validator.validator_field(update_data, rule)

    if update_data['start_route_branch_id'] or update_data['end_route_branch_id']:
        if not update_data['start_route_branch_id']:
            field_validator.append({
                "field": "start_route_branch_id",
                "message": "Start route can't be empty"})
        if not update_data['end_route_branch_id']:
            field_validator.append({
                "field": "end_route_branch_id",
                "message": "End route can't be empty"})

    if update_data['is_use_route'] == 0:
        if not update_data['route']:
            update_data['route'] = None

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    id_user = update_data['user_id']
    date = update_data['date'].split(" ")[0]

    # if delivery_controller.check_delivery_plan(id_user, date, plan_id):
    #     field_validator.append({"field": "user_id", "message": "User is already use in this date"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    del update_data['create_date'], update_data['update_date']

    if permissions == 1:
        edit_data = {
            "id": plan_id,
            "edit_data": json.dumps(update_data)
        }
        try:
            result = delivery_controller.update_delivery_plan(edit_data, plan_id)

            response['error'] = 0
            response['message'] = 'Success request update delivery plan'
            result = update_data
            create_data = {
                "prefix": "delivery/plan",
                "data_id": plan_id,
                "type": "edit",
                "data": {
                    "id": plan_id,
                    "user_id": result['user_id'],
                    "asset_id": result['asset_id'],
                    "date": result['date'],
                    "route": result['route'],
                    "destination": result['destination'],
                    "start_route_branch_id": result['start_route_branch_id'],
                    "end_route_branch_id": result['end_route_branch_id'],
                    "packing_slip_id": result['packing_slip_id']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    elif permissions == 2 or permissions == 3:
        try:
            if update_data['route'] is not None:
                update_data['route'] = json.dumps(update_data['route'])
            result = delivery_controller.update_delivery_plan(update_data, plan_id)

            response['error'] = 0
            response['message'] = 'Success update delivery plan'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/delivery/plan/<plan_id>/approve', methods=["PUT"])
@jwt_required()
def update_delivery_plan_approve(plan_id):
    """
    Approve `Create, Edit, Delete` Delivery Plan
    :example:
    :param plan_id:
    :return:

    """
    user_id = current_identity.id
    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-delivery-route']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
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
                "id": plan_id,
                "is_approval": True,
                "approval_by": user_id
            }
            try:
                delivery_plan = delivery_controller.update_delivery_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success approve create delivery plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            visit_plan = delivery_controller.get_delivery_plan_by_id(plan_id)
            edit_data = visit_plan['edit_data']
            if edit_data['route'] is not None:
                edit_data['route'] = json.dumps(edit_data['route'])
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                delivery_plan = delivery_controller.update_delivery_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success approve edit delivery plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = delivery_controller.get_delivery_plan_by_id(plan_id)
            count_delete = delivery_controller.get_delivery_plan_delete_count(result['user_id'], result['date'])
            if count_delete:
                count_delete += 1
                update_data = {
                    "id": plan_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                update_data = {
                    "id": plan_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                result = delivery_controller.update_delivery_plan(update_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success approve delete delivery plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            plan_id, type_approve['type_approve'], "delivery/plan"
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


@bp.route('/delivery/plan/<plan_id>/reject', methods=["PUT"])
@jwt_required()
def update_delivery_plan_reject(plan_id):
    """
    Approve `Create, Edit, Delete` Delivery Plan
    :example:
    :param plan_id:
    :return:

    """
    user_id = current_identity.id
    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-delivery-route']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
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
            result = delivery_controller.get_delivery_plan_by_id(plan_id)
            count_delete = delivery_controller.get_delivery_plan_delete_count(result['user_id'], result['date'])
            if count_delete:
                count_delete += 1
                edit_data = {
                    "id": plan_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": count_delete
                }
            else:
                edit_data = {
                    "id": plan_id,
                    "is_deleted": True,
                    "is_delete_approval_by": user_id,
                    "is_delete_count": 1
                }
            try:
                delivery_plan = delivery_controller.update_delivery_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success reject create delivery plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            edit_data = {
                "id": plan_id,
                "edit_data": None
            }
            try:
                delivery_plan = delivery_controller.update_delivery_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success reject edit delivery plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            update_data = {
                "id": plan_id,
                "is_delete_approval": False
            }
            try:
                result = delivery_controller.update_delivery_plan(update_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success reject delete delivery plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            plan_id, type_approve['type_approve'], "delivery/plan"
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


@bp.route('/delivery/plan', methods=["GET"])
@jwt_required()
def get_all_delivery_plan():
    """
    Get List all Delivery Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

    branch_privilege = current_identity.branch_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    if request.args.get('user_id'):
        user_id = request.args.get('user_id')

    plan_id = None
    if request.args.get('plan_id'):
        plan_id = request.args.get('plan_id')

    type = 'mobile'
    if request.args.get('type'):
        type = 'web'

    if type == 'web':
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
        result = delivery_controller.get_all_delivery_plan_data(
            page=page, limit=limit, search=search, column=column, user_id=None, direction=direction,
            branch_privilege=branch_privilege, data_filter=data_filter
        )
    else:
        if plan_id:
            result = delivery_controller.get_delivery_plan_by_user_date(_id=user_id, plan_id=plan_id)
        else:
            result = None

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/delivery/plan/list', methods=["GET"])
@jwt_required()
def get_all_list_delivery_plan():
    """
    Get List all Delivery Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

    branch_privilege = current_identity.branch_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    result = delivery_controller.get_delivery_plan_list_by_user_date(_id=user_id)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/delivery/plan/approval', methods=["GET"])
@jwt_required()
def get_all_delivery_plan_approval():
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

    branch_privilege = current_identity.branch_privilege

    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-delivery-route']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
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

    result = approval_controller.get_all_approval_data_privilege(
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='delivery/plan',
        permission=permission, branch_privilege=branch_privilege, division_privilege=None
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/delivery/plan/<plan_id>/<customer_code>', methods=["GET"])
@jwt_required()
def get_delivery_plan_customer(plan_id, customer_code):
    """
    Get List all Delivery Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    delivery_plan = delivery_controller.get_delivery_plan_by_user_date(_id=user_id, plan_id=plan_id)
    destination = delivery_plan['destination']

    result = {}
    for rec in destination:
        if rec['customer_code'] == customer_code:
            result = rec
            break

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/delivery/plan/<plan_id>/packingslip/confirm', methods=["PUT"])
@jwt_required()
def confirm_delivery_plan_packingslip(plan_id):
    """
    Confirm Packing Slip
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    delivery_plan = delivery_controller.get_delivery_plan_by_id(plan_id)
    invoice = delivery_plan['packing_slip_id']

    edit_data = dict()
    edit_data['id'] = plan_id
    edit_data['packing_slip_id'] = []
    for rec in invoice:
        if rec['id_packing_slip'] in update_data["packing_slip_id"]:
            data = {
                "id_packing_slip": rec['id_packing_slip'],
                "is_confirm": 1
            }
        else:
            data = {
                "id_packing_slip": rec['id_packing_slip'],
                "is_confirm": 0
            }
        edit_data['packing_slip_id'].append(data)

    # response['error'] = 0
    # response['data'] = edit_data
    try:
        result = delivery_controller.update_delivery_plan(edit_data, plan_id)

        response['error'] = 0
        response['message'] = 'Success update delivery plan'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)


@bp.route('/delivery/plan/<plan_id>/add/route', methods=["PUT"])
@jwt_required()
def new_route_delivery_plan(plan_id):
    """
    Confirm invoice
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/delivery/plan/<plan_id>/add/route"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()
    customer_controller = CustomerController()
    logistic_activity = LogisticActivityController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 500, 1, data=[])

    delivery_plan = delivery_controller.get_delivery_plan_by_id(plan_id)
    customer = customer_controller.get_customer_by_id(update_data['code'])
    activity = logistic_activity.check_tap_activity_by_delivery_plan(plan_id, user_id)

    destination = delivery_plan['destination']
    destination_order = delivery_plan['destination_order']

    # TODO: Get actual order has been visited
    last_activity = activity[0]
    if last_activity['tap_nfc_type'] == 'START':
        customer_order = 1
    elif last_activity['tap_nfc_type'] == 'STOP':
        raise BadRequest("Can't add new route cause you have finished plan", 500, 1, data=[])
    else:
        destination_data = next(item for item in destination_order if item["nfc_code"] == last_activity['nfc_code'])
        customer_order = destination_data['order'] + 1

    edit_data = dict()
    edit_data['id'] = plan_id

    edit_data['destination_order'] = []
    for rec in destination_order:
        data = rec
        if rec['order'] >= customer_order:
            data['order'] += 1
        edit_data['destination_order'].append(data)
    new_route = {
        'nfc_code': customer['code'],
        'order': customer_order,
        'lat': customer['lat'],
        'lng': customer['lng']
    }
    edit_data['destination_order'].append(new_route)

    edit_data['destination'] = []
    for rec_d in destination:
        data_d = rec_d
        if rec_d['order_route']:
            if rec_d['order_route'] >= customer_order:
                data_d['order_route'] += 1
        edit_data['destination'].append(data_d)
    new_destination_route = {
        "lat": customer['lat'],
        "lng": customer['lng'],
        "note": None,
        "nfcid": customer['code'],
        "phone": customer['lat'],
        "address": customer['address'],
        "packing_slip": [],
        "pic_name": customer['contacts'][0]['name'],
        "pic_phone": customer['contacts'][0]['phone'],
        "pic_mobile": customer['contacts'][0]['mobile'],
        "order_route": customer_order,
        "customer_code": customer['code'],
        "customer_name": customer['name'],
        "total_packing_slip": 0,
        "customer_email": customer['email'],
        "pic_job_position": customer['contacts'][0]['job_position'],
        "is_new": 1
    }
    edit_data['destination'].append(new_destination_route)

    try:
        delivery_plan = delivery_controller.update_delivery_plan(edit_data, plan_id)

        response['error'] = 0
        response['message'] = 'Success update delivery plan'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)



@bp.route('/delivery/plan/<plan_id>', methods=["GET"])
@jwt_required()
def get_delivery_plan(plan_id):
    """
    Get Data Delivery Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    delivery_controller = DeliveryController()
    result = delivery_controller.get_delivery_plan_by_id(plan_id)

    response['error'] = 0
    response['data'] = result
    return jsonify(response)


@bp.route('/delivery/plan/<plan_id>', methods=["DELETE"])
@jwt_required()
def delete_delivery_plan(plan_id):
    """
    Delete delivery plan
    :example:

    :param cycle_id:
    :return:
    """
    user_id = current_identity.id

    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['logistic']['data']['logistic-activities']['data'][
        'logistic-activities-delivery-route']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['logistic']['data']['logistic-activities']['data'][
                'logistic-activities-delivery-route']
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
            "id": plan_id,
            "is_delete_approval": True,
        }
        try:
            plan = delivery_controller.update_delivery_plan(update_data, plan_id)
            response['error'] = 0
            response['message'] = 'Success request delete delivery plan'

            result = delivery_controller.get_delivery_plan_by_id(plan_id)
            create_data = {
                "prefix": "delivery/plan",
                "data_id": plan_id,
                "type": "delete",
                "data": {
                    "id": plan_id,
                    "user_id": result['user_id'],
                    "asset_id": result['asset_id'],
                    "date": result['date'],
                    "route": result['route'],
                    "destination": result['destination'],
                    "start_route_branch_id": result['start_route_branch_id'],
                    "end_route_branch_id": result['end_route_branch_id'],
                    "packing_slip_id": result['packing_slip_id']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = delivery_controller.get_delivery_plan_by_id(plan_id)
        count_delete = delivery_controller.get_delivery_plan_delete_count(result['user_id'], result['date'])
        if count_delete:
            count_delete += 1
            update_data = {
                "id": plan_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": count_delete
            }
        else:
            update_data = {
                "id": plan_id,
                "is_deleted": True,
                "is_delete_approval_by": user_id,
                "is_delete_count": 1
            }
        try:
            plan = delivery_controller.update_delivery_plan(update_data, plan_id)
            response['error'] = 0
            response['message'] = 'Success delete delivery plan'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])
    return jsonify(response)


@bp.route('/delivery/plan/<int:plan_id>/summary', methods=["GET"])
@jwt_required()
def get_all_delivery_plan_summary(plan_id):
    """
    Get List all Visit Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    delivery_plan_summary = delivery_controller.get_all_delivery_plan_summary(plan_id=plan_id)

    response['error'] = 0
    response['data'] = delivery_plan_summary

    return jsonify(response)


@bp.route('/delivery/plan/<int:plan_id>/summary/<string:customer_code>', methods=["GET"])
@jwt_required()
def get_delivery_plan_summary(plan_id, customer_code):
    """
    Get List all Visit Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    delivery_plan_summary = delivery_controller.get_delivery_plan_summary(plan_id=plan_id, customer_code=customer_code)

    response['error'] = 0
    response['data'] = delivery_plan_summary

    return jsonify(response)


@bp.route('/delivery/plan/<int:plan_id>/summary/<string:customer_code>', methods=['PUT'])
@jwt_required()
def update_delivery_plan_summary(plan_id, customer_code):
    """
    Update visit plan summary
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "cycle_data:<json>"
        "http://localhost:7091/visit/plan/12/summary"
    :endpoint:
        POST /visit/plan/<plan_id>/summary
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "Summary visit has been created"
        }
    """
    user_id = current_identity.id
    validator = Validator()

    delivery_controller = DeliveryController()
    approval_controller = ApprovalController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # TODO: Get Json Data From FE
    try:
        update_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1, data=[])

    rule = {
        "notes": {
            "required": True
        }
    }

    field_validator = validator.validator_field(update_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    summary_exist = delivery_controller.check_delivery_plan_summary(plan_id, customer_code)

    if summary_exist:
        summary_exist = summary_exist[0]
        update_data['id'] = summary_exist['id']
        update_data['plan_id'] = plan_id
        update_data['customer_code'] = customer_code
        delivery_plan = delivery_controller.update_summary_plan(update_data)
    else:
        update_data['plan_id'] = plan_id
        update_data['customer_code'] = customer_code
        delivery_plan = delivery_controller.create_summary_plan(update_data, user_id)

    if delivery_plan:
        response['error'] = 0
        response['message'] = 'Success create or update delivery plan summary'
    else:
        raise BadRequest('Failed create or update delivery plan summary', 500, 1, data=[])

    return jsonify(response)


@bp.route('/delivery/<string:customer_code>', methods=["GET"])
@jwt_required()
def get_delivery_by_customer(customer_code):
    """
    Get Data Delivery Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

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

    result = delivery_controller.get_all_delivery_data(
        page=page, limit=limit, search=search, column=column, direction=direction, customer_code=customer_code
    )

    response['error'] = 0
    response['data'] = result
    return jsonify(response)


@bp.route('/delivery/<int:delivery_id>/<string:customer_code>', methods=["GET"])
@jwt_required()
def get_delivery_by_delivery_customer(delivery_id, customer_code):
    """
    Get Data Delivery Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    if request.args.get('page'):
        page = int(request.args.get('page'))
    else:
        page = 1
    if request.args.get('limit'):
        limit = int(request.args.get('limit'))
    else:
        limit = 10000
    search = None
    column = None
    direction = None
    if request.args.get('search'):
        search = request.args.get('search')
    if request.args.get('order_by_column'):
        column = request.args.get('order_by_column')
        direction = request.args.get('order_direction')

    result = delivery_controller.get_all_delivery_by_plan_customer_data(
        page=page, limit=limit, search=search, column=column, direction=direction, plan_id=delivery_id,
        customer_code=customer_code
    )

    response['error'] = 0
    response['data'] = result
    return jsonify(response)


@bp.route('/delivery/<int:delivery_id>', methods=["GET"])
@jwt_required()
def get_delivery_by_delivery_id(delivery_id):
    """
    Get Data Delivery Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/cycle"
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
                "total_filter":<int>,
                "data":<list object>
            }
        }
    """
    delivery_controller = DeliveryController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # if request.args.get('page'):
    #     page = int(request.args.get('page'))
    # else:
    #     page = 1
    # if request.args.get('limit'):
    #     limit = int(request.args.get('limit'))
    # else:
    #     limit = 10000
    # search = None
    # column = None
    # direction = None
    # if request.args.get('search'):
    #     search = request.args.get('search')
    # if request.args.get('order_by_column'):
    #     column = request.args.get('order_by_column')
    #     direction = request.args.get('order_direction')
    #
    # result = delivery_controller.get_all_delivery_by_plan_customer_data(
    #     page=page, limit=limit, search=search, column=column, direction=direction, plan_id=delivery_id,
    #     customer_code=None
    # )

    result = delivery_controller.get_delivery_by_delivery_id(delivery_id)

    response['error'] = 0
    response['data'] = result
    return jsonify(response)
