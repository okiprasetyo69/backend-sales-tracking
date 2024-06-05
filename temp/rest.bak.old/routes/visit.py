import re
import json
import requests

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity
from werkzeug.utils import secure_filename
from datetime import datetime

from rest.exceptions import BadRequest
from rest.helpers import Validator, allowed_file
from rest.controllers import VisitController, BranchesController, CustomerController, SalesController, \
    ApprovalController, SalesActivityController

__author__ = 'junior'

bp = Blueprint(__name__, "visit")


# TODO: routes for Visit Cycle
@bp.route('/visit/cycle/import', methods=['POST'])
@jwt_required()
def import_visit_cycle_file():
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
    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-visit-cycle']
    permissions = setting['rule'][4]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
            permissions = setting['rule'][4]
        else:
            permissions = 0

    visit_controller = VisitController()
    # table_name = 'visit'
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
            result = visit_controller.import_visit_cycle(import_file, user_id)

            response['error'] = 0
            response['message'] = 'Import Success'
        else:
            raise BadRequest('Extension not allowed', 422, 1, data=[])
    else:
        raise BadRequest("You don't have permission", 403, 1, data=[])

    return jsonify(response)


@bp.route('/visit/cycle', methods=['POST'])
@jwt_required()
def create_visit_cycle():
    """
    Create new visit cycle
    :example:
        curl -i -x POST
        -H "Authorization:JWT <token>"
        -H "Content-Type:multipart/form-data"
        -F "cycle_data:<json>"
        "http://localhost:7091/visit/cycle"
    :endpoint:
        POST /visit/cycle
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

    visit_controller = VisitController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-visit-cycle']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
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
        "user_id": {
            "required": True
        },
        "cycle_number": {
            "numeric": True,
            "required": True
        }
    }

    field_validator = validator.validator_field(request_data, rule)
    if request_data['cycle_number']:
        try:
            if int(request_data['cycle_number']) < 1:
                field_validator.append({"field": "cycle_number", "message": "Can't less than 1"})
        except:
            raise BadRequest("validasi", 422, 1, data=[{"field": "cycle_number", "message": "Must be numeric"}])

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

                # validation route for both use_route or not use_route (not only when is_use_route=1)
                # if not request_data[field]['route']:
                #     if request_data[field]['destination']:
                #         if not request_data[field]['destination_order']:
                #             if request_data[field]['is_use_route'] == 1:
                #                 message = "Please generate route for {0}".format(field)
                #             else:
                #                 message = "Please Draw Pin Point for {0}".format(field)
                #             field_validator.append({
                #                 "field": "cycle_{0}.route".format(day),
                #                 "message": message})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    id_user = request_data['user_id']
    cycle_no = request_data['cycle_number']
    if visit_controller.check_visit_cycle_by_user_cycle(id_user, cycle_no, None):
        field_validator.append({"field": "user_id", "message": "User is already used in cycle number"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    visit_cycle = visit_controller.create(request_data, user_id)

    if visit_cycle:
        response['error'] = 0
        response['message'] = 'Success create visit cycle'
        if permission == 1:
            result = visit_controller.get_visit_cycle_by_id(visit_cycle)
            create_data = {
                "prefix": "visit/cycle",
                "data_id": visit_cycle,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "user_id": result['user_id'],
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
                result = visit_controller.rollback_cycle_insert(visit_cycle)
                print("Visit Cycle deleted")
    else:
        raise BadRequest('Failed create visit cycle', 500, 1, data=[])

    return jsonify(response)


@bp.route('/visit/cycle', methods=["GET"])
@jwt_required()
def get_all_visit_cycle():
    """
    Get List all Visit Cycle
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
    visit_controller = VisitController()

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
    visit_cycle = visit_controller.get_all_visit_cycle_data(
        page=page, limit=limit, search=search, column=column, direction=direction, branch_privilege=branch_privilege,
        division_privilege=division_privilege
    )

    response['error'] = 0
    response['data'] = visit_cycle

    return jsonify(response)


@bp.route('/visit/cycle/approval', methods=["GET"])
@jwt_required()
def get_all_visit_cycle_approval():
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
    division_privilege = current_identity.division_privilege

    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-visit-cycle']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='visit/cycle',
        permission=permission, branch_privilege=branch_privilege, division_privilege=division_privilege
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/visit/cycle/<cycle_id>', methods=["GET"])
@jwt_required()
def get_visit_cycle_by_id(cycle_id):
    """
    Get Visit Cycle Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    visit_controller = VisitController()
    visit_cycle = visit_controller.get_visit_cycle_by_id(cycle_id)

    response['error'] = 0
    response['data'] = visit_cycle
    return jsonify(response)


@bp.route('/visit/cycle/<cycle_id>', methods=["PUT"])
@jwt_required()
def update_visit_cycle(cycle_id):
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
    visit_controller = VisitController()
    approval_controller = ApprovalController()

    validator = Validator()
    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-visit-cycle']
    permissions = setting['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
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

    if update_data['cycle_number']:
        try:
            if int(update_data['cycle_number']) < 1:
                field_validator.append({"field": "cycle_number", "message": "Can't less than 1"})
        except:
            raise BadRequest("validasi", 422, 1, data=[{"field": "cycle_number", "message": "Must be numeric"}])

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

            # validation is_use_route
            # if update_data[field]['is_use_route'] == 1:
            #     if not update_data[field]['destination']:
            #         field_validator.append({
            #             "field": "cycle_{0}.destination".format(day),
            #             "message": "Destination {0} can't be empty".format(field)})
            #     if not update_data[field]['route']:
            #         field_validator.append({
            #             "field": "cycle_{0}.route".format(day),
            #             "message": "Please generate route for {0}".format(field)})
            #
            # # clear destination and destination_order
            # if update_data[field]['is_use_route'] == 0:
            #     update_data[field]['route'] = None
            #     update_data[field]['destination_order'] = None

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    id_user = update_data['user_id']
    cycle_no = update_data['cycle_number']

    if visit_controller.check_visit_cycle_by_user_cycle(id_user, cycle_no, cycle_id):
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
            visit_cycle = visit_controller.update_visit_cycle(edit_data, cycle_id)

            response['error'] = 0
            response['message'] = 'Success request update visit cycle'
            result = update_data
            create_data = {
                "prefix": "visit/cycle",
                "data_id": cycle_id,
                "type": "edit",
                "data": {
                    "id": cycle_id,
                    "user_id": result['user_id'],
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
            visit_cycle = visit_controller.update_visit_cycle(update_data, cycle_id)

            response['error'] = 0
            response['message'] = 'Success update visit cycle'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/visit/cycle/<cycle_id>/approve', methods=["PUT"])
@jwt_required()
def update_visit_cycle_approve(cycle_id):
    """
    Approve `Create, Edit, Delete` Visit Cycle
    :example:
    :param cycle_id:
    :return:

    """
    user_id = current_identity.id
    visit_controller = VisitController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-visit-cycle']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
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
                visit_cycle = visit_controller.update_visit_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success approve create visit cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            visit_cycle = visit_controller.get_visit_cycle_by_id(cycle_id)
            edit_data = visit_cycle['edit_data']
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
                visit_cycle = visit_controller.update_visit_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success approve edit visit cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = visit_controller.get_visit_cycle_by_id(cycle_id)
            count_delete = visit_controller.get_visit_cycle_delete_count(result['user_id'], result['cycle_number'])
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
                result = visit_controller.update_visit_cycle(update_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success approve delete visit cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            cycle_id, type_approve['type_approve'], "visit/cycle"
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


@bp.route('/visit/cycle/<cycle_id>/reject', methods=["PUT"])
@jwt_required()
def update_visit_cycle_reject(cycle_id):
    """
    Approve `Create, Edit, Delete` Visit Cycle
    :example:
    :param cycle_id:
    :return:

    """
    user_id = current_identity.id
    visit_controller = VisitController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-visit-cycle']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
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
            result = visit_controller.get_visit_cycle_by_id(cycle_id)
            count_delete = visit_controller.get_visit_cycle_delete_count(result['user_id'], result['cycle_number'])
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
                visit_cycle = visit_controller.update_visit_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success reject create visit cycle'
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
                visit_cycle = visit_controller.update_visit_cycle(edit_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success reject edit visit cycle'
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
                result = visit_controller.update_visit_cycle(update_data, cycle_id)

                response['error'] = 0
                response['message'] = 'Success reject delete visit cycle'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            cycle_id, type_approve['type_approve'], "visit/cycle"
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


@bp.route('/visit/cycle/<cycle_id>', methods=["DELETE"])
@jwt_required()
def delete_visit_cycle(cycle_id):
    """
    Delete visit cycle
    :example:

    :param cycle_id:
    :return:
    """
    user_id = current_identity.id
    visit_controller = VisitController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['sales']['data']['sales-data']['data']['sales-data-visit-cycle']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['sales']['data']['sales-data']['data'][
                'sales-data-visit-cycle']
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
            "id": cycle_id,
            "is_delete_approval": True,
        }
        try:
            cycle = visit_controller.update_visit_cycle(update_data, cycle_id)
            response['error'] = 0
            response['message'] = 'Success request delete visit cycle'

            result = visit_controller.get_visit_cycle_by_id(cycle_id)
            create_data = {
                "prefix": "visit/cycle",
                "data_id": cycle_id,
                "type": "delete",
                "data": {
                    "id": cycle_id,
                    "user_id": result['user_id'],
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
        result = visit_controller.get_visit_cycle_by_id(cycle_id)
        count_delete = visit_controller.get_visit_cycle_delete_count(result['user_id'], result['cycle_number'])
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
            cycle = visit_controller.update_visit_cycle(update_data, cycle_id)
            response['error'] = 0
            response['message'] = 'Success delete visit cycle'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])
    return jsonify(response)


# TODO: Route for visit plan
@bp.route('/visit/plan/generate', methods=['POST'])
@jwt_required()
def generate_visit_plan():
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
    visit_controller = VisitController()
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
    visit_plan = visit_controller.generate(request_data, id_user)

    if visit_plan:
        response['error'] = 0
        response['message'] = 'Success generate visit plan'
    else:
        raise BadRequest('Failed generate visit plan', 500, 1, data=[])

    return jsonify(response)


@bp.route('/visit/plan', methods=['POST'])
@jwt_required()
def create_visit_plan():
    """
    Create new visit plan
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

    visit_controller = VisitController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['sales']['data']['sales-activities']['data']['sales-activities-visit-plan']
    permission = setting['rule'][1]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
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
    # if visit_controller.check_visit_plan(id_user, date, None):
    #     field_validator.append({"field": "user_id", "message": "User is already use in this date"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    visit_plan = visit_controller.create_visit_plan(request_data, user_id)

    if visit_plan:
        response['error'] = 0
        response['message'] = 'Success create visit plan'
        if permission == 1:
            result = visit_controller.get_visit_plan_by_id(visit_plan)
            create_data = {
                "prefix": "visit/plan",
                "data_id": visit_plan,
                "type": "create",
                "data": {
                    "id": result['id'],
                    "user_id": result['user_id'],
                    "date": result['date'],
                    "route": result['route'],
                    "destination": result['destination'],
                    "start_route_branch_id": result['start_route_branch_id'],
                    "end_route_branch_id": result['end_route_branch_id'],
                    "invoice_id": result['invoice_id'],
                    "is_use_route": result['is_use_route']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
                result = visit_controller.rollback_plan_insert(visit_plan)
                raise BadRequest('Failed create visit plan', 500, 1, data=[])
    else:
        raise BadRequest('Failed create visit plan', 500, 1, data=[])

    return jsonify(response)


@bp.route('/visit/plan/<plan_id>', methods=["PUT"])
@jwt_required()
def update_visit_plan(plan_id):
    """
    Update Visit Plan Data By id
    :example:

    :return:
    """
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    visit_controller = VisitController()
    approval_controller = ApprovalController()

    validator = Validator()
    setting = current_identity.permissions['sales']['data']['sales-activities']['data']['sales-activities-visit-plan']
    permissions = setting['rule'][2]

    if permissions == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
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

    # if visit_controller.check_visit_plan(id_user, date, plan_id):
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
            visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

            response['error'] = 0
            response['message'] = 'Success request update visit plan'
            result = update_data
            create_data = {
                "prefix": "visit/plan",
                "data_id": plan_id,
                "type": "edit",
                "data": {
                    "id": plan_id,
                    "user_id": result['user_id'],
                    "date": result['date'],
                    "route": result['route'],
                    "destination": result['destination'],
                    "start_route_branch_id": result['start_route_branch_id'],
                    "end_route_branch_id": result['end_route_branch_id'],
                    "invoice_id": result['invoice_id']
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
            visit_cycle = visit_controller.update_visit_plan(update_data, plan_id)

            response['error'] = 0
            response['message'] = 'Success update visit plan'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
        return jsonify(response)
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])


@bp.route('/visit/plan/<plan_id>/approve', methods=["PUT"])
@jwt_required()
def update_visit_plan_approve(plan_id):
    """
    Approve `Create, Edit, Delete` Visit Cycle
    :example:
    :param plan_id:
    :return:

    """
    user_id = current_identity.id
    visit_controller = VisitController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['sales']['data']['sales-activities']['data']['sales-activities-visit-plan']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
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
                visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success approve create visit plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'edit':
        if permission[2] == 3:
            visit_plan = visit_controller.get_visit_plan_by_id(plan_id)
            edit_data = visit_plan['edit_data']
            if edit_data['route'] is not None:
                edit_data['route'] = json.dumps(edit_data['route'])
            edit_data["approval_by"] = user_id
            edit_data["edit_data"] = None
            try:
                visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success approve edit visit plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    elif type_approve['type_approve'] == 'delete':
        if permission[3] == 3:
            result = visit_controller.get_visit_plan_by_id(plan_id)
            count_delete = visit_controller.get_visit_plan_delete_count(result['user_id'], result['date'])
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
                result = visit_controller.update_visit_plan(update_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success approve delete visit plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            plan_id, type_approve['type_approve'], "visit/plan"
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


@bp.route('/visit/plan/<plan_id>/reject', methods=["PUT"])
@jwt_required()
def update_visit_plan_reject(plan_id):
    """
    Approve `Create, Edit, Delete` Visit Cycle
    :example:
    :param plan_id:
    :return:

    """
    user_id = current_identity.id
    visit_controller = VisitController()
    approval_controller = ApprovalController()

    today = datetime.today()
    today = today.strftime("%Y-%m-%d %H:%M:%S")

    setting = current_identity.permissions['sales']['data']['sales-activities']['data']['sales-activities-visit-plan']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
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
            result = visit_controller.get_visit_plan_by_id(plan_id)
            count_delete = visit_controller.get_visit_plan_delete_count(result['user_id'], result['date'])
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
                visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success reject create visit plan'
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
                visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success reject edit visit plan'
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
                result = visit_controller.update_visit_plan(update_data, plan_id)

                response['error'] = 0
                response['message'] = 'Success reject delete visit plan'
            except Exception as e:
                raise BadRequest(e, 500, 1, data=[])
        else:
            raise BadRequest('Access Not Authorized', 401, 1, data=[])
    else:
        raise BadRequest("Please input type for approve", 422, 1, data=[])

    try:
        result = approval_controller.get_approval_by_data_id_and_type(
            plan_id, type_approve['type_approve'], "visit/plan"
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


@bp.route('/visit/plan', methods=["GET"])
@jwt_required()
def get_all_visit_plan():
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
    visit_controller = VisitController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id
    if request.args.get('user_id'):
        user_id = request.args.get('user_id')
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

        visit_plan = visit_controller.get_all_visit_plan_data(
            page=page, limit=limit, search=search, column=column, user_id=None, direction=direction,
            branch_privilege=branch_privilege, division_privilege=division_privilege, data_filter=data_filter
        )
    else:
        visit_plan = visit_controller.get_visit_plan_by_user_date(_id=user_id)

    response['error'] = 0
    response['data'] = visit_plan

    return jsonify(response)


@bp.route('/visit/plan/approval', methods=["GET"])
@jwt_required()
def get_all_visit_plan_approval():
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
    division_privilege = current_identity.division_privilege

    setting = current_identity.permissions['sales']['data']['sales-activities']['data']['sales-activities-visit-plan']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
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
        page=page, limit=limit, search=search, column=column, direction=direction, prefix='visit/plan',
        permission=permission, branch_privilege=branch_privilege, division_privilege=division_privilege
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/visit/plan/<plan_id>/<customer_code>', methods=["GET"])
@jwt_required()
def get_visit_plan_customer(plan_id, customer_code):
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
    visit_controller = VisitController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    visit_plan = visit_controller.get_visit_plan_by_user_date(_id=user_id)
    destination = visit_plan['destination']
    if visit_plan['destination_new'] is not None:
        new_destination = visit_plan['destination_new']
        for new in new_destination:
            destination.append(new)

    result = {}
    for rec in destination:
        if rec['customer_code'] == customer_code:
            result = rec
            break

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/visit/plan/<plan_id>/request', methods=["GET"])
@jwt_required()
def get_visit_plan_request(plan_id):
    """
    Get List all Visit Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/plan/<plan_id>/invoice"
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
    visit_controller = VisitController()
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    visit_plan = visit_controller.get_visit_plan_by_id(_id=plan_id)
    destination = visit_plan['destination']
    if visit_plan['destination_new'] is not None:
        new_destination = visit_plan['destination_new']
        for new in new_destination:
            destination.append(new)

    list_customer = []
    for rec in destination:
        list_customer.append(rec['customer_code'])

    result = sales_controller.get_all_sales_request_by_list_customer(
        page=1, limit=1000, customer=list_customer, user_id=user_id, username=None
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/visit/plan/<plan_id>/order', methods=["GET"])
@jwt_required()
def get_visit_plan_order(plan_id):
    """
    Get List all Visit Plan
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/visit/plan/<plan_id>/invoice"
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
    visit_controller = VisitController()
    sales_controller = SalesController()
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    user_id = current_identity.id

    visit_plan = visit_controller.get_visit_plan_by_id(_id=plan_id)
    destination = visit_plan['destination']
    if visit_plan['destination_new'] is not None:
        new_destination = visit_plan['destination_new']
        for new in new_destination:
            destination.append(new)

    list_customer = []
    for rec in destination:
        list_customer.append(rec['customer_code'])

    result = sales_controller.get_all_sales_order_by_list_customer(
        page=1, limit=1000, customer=list_customer, user_id=user_id, username=None
    )

    response['error'] = 0
    response['data'] = result

    return jsonify(response)


@bp.route('/visit/plan/<plan_id>/invoice/confirm', methods=["PUT"])
@jwt_required()
def confirm_visit_plan_invoice(plan_id):
    """
    Confirm invoice
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
    visit_controller = VisitController()
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

    visit_plan = visit_controller.get_visit_plan_by_id(plan_id)
    invoice = visit_plan['invoice_id']

    edit_data = dict()
    edit_data['id'] = plan_id
    edit_data['invoice_id'] = []
    for rec in invoice:
        if rec['id_invoice'] in update_data["invoice_id"]:
            data = {
                "id_invoice": rec['id_invoice'],
                "is_confirm": 1
            }
        else:
            data = {
                "id_invoice": rec['id_invoice'],
                "is_confirm": 0
            }
        edit_data['invoice_id'].append(data)

    # response['error'] = 0
    # response['data'] = edit_data
    try:
        visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

        response['error'] = 0
        response['message'] = 'Success update visit plan'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)


@bp.route('/visit/plan/<plan_id>/add/route', methods=["PUT"])
@jwt_required()
def new_route_visit_plan(plan_id):
    """
    Confirm invoice
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
    visit_controller = VisitController()
    customer_controller = CustomerController()
    sales_activity = SalesActivityController()
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

    visit_plan = visit_controller.get_visit_plan_by_id(plan_id)
    customer = customer_controller.get_customer_by_id(update_data['code'])

    # TODO: If use destination already exist
    # activity = sales_activity.check_tap_activity_by_visit_plan(plan_id, user_id)
    #
    # destination = visit_plan['destination']
    # destination_order = visit_plan['destination_order']
    #
    # TODO: Get actual order has been visited
    # last_activity = activity[0]
    # if last_activity['tap_nfc_type'] == 'START':
    #     customer_order = 1
    # elif last_activity['tap_nfc_type'] == 'STOP':
    #     raise BadRequest("Can't add new route cause you have finished plan", 500, 1, data=[])
    # else:
    #     destination_data = next(item for item in destination_order if item["nfc_code"] == last_activity['nfc_code'])
    #     customer_order = destination_data['order'] + 1
    #
    # edit_data = dict()
    # edit_data['id'] = plan_id
    #
    # edit_data['destination_order'] = []
    # for rec in destination_order:
    #     data = rec
    #     if rec['order'] >= customer_order:
    #         data['order'] += 1
    #     edit_data['destination_order'].append(data)
    # new_route = {
    #     'nfc_code': customer['code'],
    #     'order': customer_order,
    #     'lat': customer['lat'],
    #     'lng': customer['lng']
    # }
    # edit_data['destination_order'].append(new_route)
    #
    # edit_data['destination'] = []
    # for rec_d in destination:
    #     data_d = rec_d
    #     if rec_d['order_route']:
    #         if rec_d['order_route'] >= customer_order:
    #             data_d['order_route'] += 1
    #     edit_data['destination'].append(data_d)
    # new_destination_route = {
    #     "lat": customer['lat'],
    #     "lng": customer['lng'],
    #     "note": None,
    #     "nfcid": customer['code'],
    #     "phone": customer['lat'],
    #     "address": customer['address'],
    #     "invoice": [],
    #     "pic_name": customer['contacts'][0]['name'],
    #     "pic_phone": customer['contacts'][0]['phone'],
    #     "pic_mobile": customer['contacts'][0]['mobile'],
    #     "order_route": customer_order,
    #     "customer_code": customer['code'],
    #     "customer_name": customer['name'],
    #     "total_invoice": 0,
    #     "customer_email": customer['email'],
    #     "pic_job_position": customer['contacts'][0]['job_position'],
    #     "is_new": 1
    # }
    # edit_data['destination'].append(new_destination_route)

    # TODO: If use new column in db
    destination_new = visit_plan['destination_new']
    edit_data = dict()
    edit_data['id'] = plan_id
    edit_data['is_use_route'] = visit_plan['is_use_route']
    # edit_data['destination'] = []
    edit_data['destination_new'] = []
    new_destination_route = {
        "lat": customer['lat'],
        "lng": customer['lng'],
        "note": None,
        "nfcid": customer['code'],
        "phone": customer['lat'],
        "address": customer['address'],
        "invoice": [],
        "pic_name": customer['contacts'][0]['name'],
        "pic_phone": customer['contacts'][0]['phone'],
        "pic_mobile": customer['contacts'][0]['mobile'],
        "customer_code": customer['code'],
        "customer_name": customer['name'],
        "total_invoice": 0,
        "customer_email": customer['email'],
        "pic_job_position": customer['contacts'][0]['job_position']
    }
    if destination_new:
        for rec in destination_new:
            edit_data['destination_new'].append(rec)
    edit_data['destination_new'].append(new_destination_route)
    try:
        visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

        response['error'] = 0
        response['message'] = 'Success update visit plan'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)


@bp.route('/visit/plan/<plan_id>', methods=["GET"])
@jwt_required()
def get_visit_plan(plan_id):
    """
    Get Data Visit Plan
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
    visit_controller = VisitController()
    visit_plan = visit_controller.get_visit_plan_by_id(plan_id)

    response['error'] = 0
    response['data'] = visit_plan
    return jsonify(response)


@bp.route('/visit/plan/<plan_id>', methods=["DELETE"])
@jwt_required()
def delete_visit_plan(plan_id):
    """
    Delete visit plan
    :example:

    :param plan_id:
    :return:
    """
    user_id = current_identity.id
    visit_controller = VisitController()
    approval_controller = ApprovalController()

    setting = current_identity.permissions['sales']['data']['sales-activities']['data']['sales-activities-visit-plan']
    permission = setting['rule'][3]

    if permission == 10:
        if current_identity.permissions_group is not None:
            setting = current_identity.permissions_group['sales']['data']['sales-activities']['data'][
                'sales-activities-visit-plan']
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
            "id": plan_id,
            "is_delete_approval": True,
        }
        try:
            plan = visit_controller.update_visit_plan(update_data, plan_id)
            response['error'] = 0
            response['message'] = 'Success request delete visit plan'

            result = visit_controller.get_visit_plan_by_id(plan_id)
            create_data = {
                "prefix": "visit/plan",
                "data_id": plan_id,
                "type": "delete",
                "data": {
                    "id": plan_id,
                    "user_id": result['user_id'],
                    "date": result['date'],
                    "route": result['route'],
                    "destination": result['destination'],
                    "start_route_branch_id": result['start_route_branch_id'],
                    "end_route_branch_id": result['end_route_branch_id'],
                    "invoice_id": result['invoice_id']
                }
            }
            try:
                result = approval_controller.create_plan(create_data, user_id)
            except Exception as e:
                print(e)
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    elif permission == 2 or permission == 3:
        result = visit_controller.get_visit_plan_by_id(plan_id)
        count_delete = visit_controller.get_visit_plan_delete_count(result['user_id'], result['date'])
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
            cycle = visit_controller.update_visit_plan(update_data, plan_id)
            response['error'] = 0
            response['message'] = 'Success delete visit plan'
        except Exception as e:
            raise BadRequest(e, 500, 1, data=[])
    else:
        raise BadRequest("Access Not Authorized", 401, 1, data=[])
    return jsonify(response)


@bp.route('/visit/plan/<int:plan_id>/summary', methods=["GET"])
@jwt_required()
def get_all_visit_plan_summary(plan_id):
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
    visit_controller = VisitController()
    user_id = current_identity.id

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    visit_plan_summary = visit_controller.get_all_visit_plan_summary(plan_id=plan_id)

    response['error'] = 0
    response['data'] = visit_plan_summary

    return jsonify(response)


@bp.route('/visit/plan/<int:plan_id>/summary/<string:customer_code>', methods=["GET"])
@jwt_required()
def get_visit_plan_summary(plan_id, customer_code):
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
    visit_controller = VisitController()
    user_id = current_identity.id

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    visit_plan_summary = visit_controller.get_visit_plan_summary(plan_id=plan_id, customer_code=customer_code)

    response['error'] = 0
    response['data'] = visit_plan_summary

    return jsonify(response)


@bp.route('/visit/plan/<int:plan_id>/summary/<string:customer_code>', methods=['PUT'])
@jwt_required()
def update_visit_plan_summary(plan_id, customer_code):
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

    visit_controller = VisitController()
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

    summary_exist = visit_controller.check_visit_plan_summary(plan_id, customer_code)

    if summary_exist:
        summary_exist = summary_exist[0]
        update_data['id'] = summary_exist['id']
        update_data['plan_id'] = plan_id
        update_data['customer_code'] = customer_code
        visit_plan = visit_controller.update_summary_plan(update_data)
    else:
        update_data['plan_id'] = plan_id
        update_data['customer_code'] = customer_code
        visit_plan = visit_controller.create_summary_plan(update_data, user_id)

    if visit_plan:
        response['error'] = 0
        response['message'] = 'Success create or update visit plan summary'
    else:
        raise BadRequest('Failed create or update visit plan summary', 500, 1, data=[])

    return jsonify(response)


@bp.route('/visit/plan/<int:plan_id>/invoice', methods=['PUT'])
@jwt_required()
def update_visit_plan_invoice(plan_id):
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

    visit_controller = VisitController()

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
        "invoice": {
            "required": True
        }
    }

    field_validator = validator.validator_field(update_data, rule)

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    visit_plan = visit_controller.get_visit_plan_by_id(plan_id)
    invoice = visit_plan['invoice_id']

    edit_data = dict()
    edit_data['id'] = plan_id
    edit_data['invoice_id'] = []
    if invoice:
        for rec in invoice:
            edit_data['invoice_id'].append(rec)
        for inv in update_data['invoice']:
            data = {
                "id_invoice": inv,
                "is_confirm": 1
            }
            edit_data['invoice_id'].append(data)
    else:
        for inv in update_data['invoice']:
            data = {
                "id_invoice": inv,
                "is_confirm": 1
            }
            edit_data['invoice_id'].append(data)

    # response['error'] = 0
    # response['data'] = edit_data
    try:
        visit_plan = visit_controller.update_visit_plan(edit_data, plan_id)

        response['error'] = 0
        response['message'] = 'Success update visit plan'
    except Exception as e:
        raise BadRequest(e, 500, 1, data=[])

    return jsonify(response)

# TODO: Route for generate route
@bp.route('/route/generate', methods=['POST'])
@jwt_required()
def generate_route():
    """
    Get Generate Route
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/route/generate"
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
    google_key = current_app.config['MAPS_KEY']
    route_url = current_app.config['MAPS_ROUTES_URL']
    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # visit_controller = VisitController()
    branch_controller = BranchesController()
    customer_controller = CustomerController()
    validator = Validator()

    data = []
    try:
        request_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "user_id": {
            "required": True
        },
        "date": {
            "required": True
        }
    }
    field_validator = validator.validator_field(request_data, rule)

    if request_data['start_route_id'] or request_data['end_route_id'] or request_data['is_use_route']:
        if request_data['start_route_id'] is None:
            field_validator.append({
                "field": "start_route_id",
                "message": "Start route can't be empty"})
        if request_data['end_route_id'] is None:
            field_validator.append({
                "field": "end_route_id",
                "message": "End route can't be empty"})
        if request_data['is_use_route'] is None:
            field_validator.append({
                "field": "is_use_route",
                "message": "Route can't be empty"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    is_use_route = request_data['is_use_route']
    if is_use_route == 1:
        waypoint = []
        waypoint_cust = []
        waypoint_order = dict()
        customer_order = []

        origin = branch_controller.get_branches_by_id(request_data['start_route_id'])
        data_origin = {
            "order": 0,
            "lat": origin['lat'],
            "lng": origin['lng'],
            "nfc_code": request_data['start_route_id']
        }
        origin = "{0},{1}".format(origin['lat'], origin['lng'])
        if request_data['destination'] is not None:
            for rec in request_data['destination']:
                customer = customer_controller.get_customer_by_id(rec['customer'])
                if rec['order_route'] is not None:
                    waypoint_order[rec["order_route"]] = {
                        "latlng": "{0},{1}".format(customer['lat'], customer['lng']),
                        "nfc_code": rec['customer']
                    }
                    # waypoint_order[rec["order_route"]]['latlng'] = "{0},{1}".format(customer['lat'], customer['lng'])
                    # waypoint_order[rec["order_route"]]['nfc_code'] = rec['customer']
                else:
                    lat_long = "{0},{1}".format(customer['lat'], customer['lng'])
                    waypoint.append(lat_long)
                    waypoint_cust.append(rec['customer'])
        dest = branch_controller.get_branches_by_id(request_data['end_route_id'])
        destination = "{0},{1}".format(dest['lat'], dest['lng'])

        customer_order.append(data_origin)
        # print(waypoint_order)
        # print(waypoint)
        # print(waypoint_cust)
        # if waypoint_order:
        #     i = 1
        #     waypoint_data = []
        #     while i <= len(waypoint_order):
        #         waypoint_data.append(waypoint_order[i])
        #         i += 1
        #
        #     if waypoint_data:
        #         if len(waypoint_order) == len(request_data['destination']):
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": destination,
        #                 "waypoints": "|".join(waypoint_data)
        #             }
        #         else:
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": waypoint_order[len(waypoint_order)],
        #                 "waypoints": "|".join(waypoint_data)
        #             }
        #     else:
        #         if len(waypoint_order) == len(request_data['destination']):
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": destination
        #             }
        #         else:
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": waypoint_order[len(waypoint_order)]
        #             }
        #     route_order_request = requests.get(url=route_url, params=route_order_payload)
        #     route_order_json = route_order_request.json()
        #     data.append(route_order_json)

        if waypoint:
            if waypoint_order:
                route_payload = {
                    "key": google_key,
                    "language": "ID",
                    "origin": waypoint_order[len(waypoint_order)]['latlng'],
                    "destination": destination,
                    "avoid": "tolls",
                    "waypoints": "optimize:true|" + "|".join(waypoint)
                }
                route_request = requests.get(url=route_url, params=route_payload)
                route_json = route_request.json()
                order_route = route_json['routes'][0]['waypoint_order']
                last_order_route = len(waypoint_order)
                for ord in order_route:
                    last_order_route += 1
                    waypoint_order[last_order_route] = {
                        "latlng": waypoint[ord],
                        "nfc_code": waypoint_cust[ord]
                    }
                    # waypoint_order[last_order_route]['latlng'] = waypoint[ord]
                    # waypoint_order[last_order_route]['nfc_code'] = waypoint_cust[ord]
            else:
                route_payload = {
                    "key": google_key,
                    "language": "ID",
                    "origin": origin,
                    "destination": destination,
                    "avoid": "tolls",
                    "waypoints": "optimize:true|" + "|".join(waypoint)
                }
                # print("=======DEBUG 1======")
                # print(waypoint_cust)
                route_request = requests.get(url=route_url, params=route_payload)
                route_json = route_request.json()
                order_route = route_json['routes'][0]['waypoint_order']
                data.append(route_json)
                i = 1
                for ord in order_route:
                    customer_data = dict()
                    customer_data['order'] = i
                    customer_data['nfc_code'] = waypoint_cust[ord]
                    latlng = waypoint[ord].split(',')
                    lat = latlng[0]
                    lng = latlng[1]
                    customer_data['lat'] = lat
                    customer_data['lng'] = lng
                    customer_order.append(customer_data)
                    i += 1

        if waypoint_order:
            i = 1
            waypoint_data = []
            while i <= len(waypoint_order):
                waypoint_data.append(waypoint_order[i]['latlng'])
                customer_data = dict()
                customer_data['order'] = i
                customer_data['nfc_code'] = waypoint_order[i]['nfc_code']
                latlng = waypoint_order[i]['latlng'].split(',')
                lat = latlng[0]
                lng = latlng[1]
                customer_data['lat'] = lat
                customer_data['lng'] = lng
                customer_order.append(customer_data)
                i += 1

            if waypoint_data:
                if len(waypoint_order) == len(request_data['destination']):
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": destination,
                        "avoid": "tolls",
                        "waypoints": "|".join(waypoint_data)
                    }
                else:
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": waypoint_order[len(waypoint_order)]['latlng'],
                        "avoid": "tolls",
                        "waypoints": "|".join(waypoint_data)
                    }
            else:
                if len(waypoint_order) == len(request_data['destination']):
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": destination,
                        "avoid": "tolls",
                    }
                else:
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": waypoint_order[len(waypoint_order)]['latlng'],
                        "avoid": "tolls",
                    }
            route_order_request = requests.get(url=route_url, params=route_order_payload)
            route_order_json = route_order_request.json()
            data.append(route_order_json)
            # print("=======DEBUG 1======")
            # print(route_order_payload)

        # print("=======DEBUG 2======")
        # print(data[0]['routes'][0]['waypoint_order'])
        # print("=======DEBUG 3======")
        # print(customer_order)
        # print("=======DEBUG 4======")
        # print(data)
        last_dest = len(customer_order)
        data_dest = {
            "order": last_dest,
            "lat": dest['lat'],
            "lng": dest['lng'],
            "nfc_code": request_data['end_route_id']
        }
        customer_order.append(data_dest)
        data.append(customer_order)
    else:
        # array[0]
        list_route = []
        data_routes = dict()
        data.append(data_routes)

        # array[1]
        # start_route
        data_routes = dict()
        start_route_branch = branch_controller.get_branches_by_id(request_data['start_route_id'])
        data_routes['lat'] = start_route_branch['lat']
        data_routes['lng'] = start_route_branch['lng']
        data_routes['nfc_code'] = start_route_branch['id']
        data_routes['order'] = 0
        list_route.append(data_routes)

        # destination
        i = 1
        if request_data['destination'] is not None:
            for rec in request_data['destination']:
                data_routes = dict()
                customer = customer_controller.get_customer_by_id(rec['customer'])
                data_routes['lat'] = customer['lat']
                data_routes['lng'] = customer['lng']
                data_routes['nfc_code'] = customer['code']
                data_routes['order'] = i
                list_route.append(data_routes)
                i += 1

        # end route
        data_routes = dict()
        end_route_branch = branch_controller.get_branches_by_id(request_data['end_route_id'])
        data_routes['lat'] = end_route_branch['lat']
        data_routes['lng'] = end_route_branch['lng']
        data_routes['nfc_code'] = end_route_branch['id']
        data_routes['order'] = i
        list_route.append(data_routes)
        data.append(list_route)

    response['error'] = 0
    response['data'] = data
    return jsonify(response)


@bp.route('/controller/route/generate', methods=['POST'])
def generate_route_from_controller():
    """
    Get Generate Route
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/route/generate"
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
    google_key = current_app.config['MAPS_KEY']
    route_url = current_app.config['MAPS_ROUTES_URL']

    response = {
        'error': 1,
        'message': '',
        'data': []
    }
    # visit_controller = VisitController()
    branch_controller = BranchesController()
    customer_controller = CustomerController()
    validator = Validator()

    data = []
    try:
        request_data = request.get_json(silent=True)
    except:
        raise BadRequest("Params is missing or error format, check double quatation", 200, 1)

    rule = {
        "user_id": {
            "required": True
        },
        "date": {
            "required": True
        }
    }
    field_validator = validator.validator_field(request_data, rule)

    if request_data['start_route_id'] or request_data['end_route_id'] or request_data['is_use_route']:
        if request_data['start_route_id'] is None:
            field_validator.append({
                "field": "start_route_id",
                "message": "Start route can't be empty"})
        if request_data['end_route_id'] is None:
            field_validator.append({
                "field": "end_route_id",
                "message": "End route can't be empty"})
        if request_data['is_use_route'] is None:
            field_validator.append({
                "field": "is_use_route",
                "message": "Route can't be empty"})

    if field_validator:
        raise BadRequest("validasi", 422, 1, data=field_validator)

    is_use_route = request_data['is_use_route']
    if is_use_route == 1:
        waypoint = []
        waypoint_cust = []
        waypoint_order = dict()
        customer_order = []

        origin = branch_controller.get_branches_by_id(request_data['start_route_id'])
        data_origin = {
            "order": 0,
            "lat": origin['lat'],
            "lng": origin['lng'],
            "nfc_code": request_data['start_route_id']
        }
        origin = "{0},{1}".format(origin['lat'], origin['lng'])
        if request_data['destination'] is not None:
            for rec in request_data['destination']:
                customer = customer_controller.get_customer_by_id(rec['customer'])
                if rec['order_route'] is not None:
                    waypoint_order[rec["order_route"]] = {
                        "latlng": "{0},{1}".format(customer['lat'], customer['lng']),
                        "nfc_code": rec['customer']
                    }
                    # waypoint_order[rec["order_route"]]['latlng'] = "{0},{1}".format(customer['lat'], customer['lng'])
                    # waypoint_order[rec["order_route"]]['nfc_code'] = rec['customer']
                else:
                    lat_long = "{0},{1}".format(customer['lat'], customer['lng'])
                    waypoint.append(lat_long)
                    waypoint_cust.append(rec['customer'])
        dest = branch_controller.get_branches_by_id(request_data['end_route_id'])
        destination = "{0},{1}".format(dest['lat'], dest['lng'])

        customer_order.append(data_origin)
        # print(waypoint_order)
        # print(waypoint)
        # print(waypoint_cust)
        # if waypoint_order:
        #     i = 1
        #     waypoint_data = []
        #     while i <= len(waypoint_order):
        #         waypoint_data.append(waypoint_order[i])
        #         i += 1
        #
        #     if waypoint_data:
        #         if len(waypoint_order) == len(request_data['destination']):
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": destination,
        #                 "waypoints": "|".join(waypoint_data)
        #             }
        #         else:
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": waypoint_order[len(waypoint_order)],
        #                 "waypoints": "|".join(waypoint_data)
        #             }
        #     else:
        #         if len(waypoint_order) == len(request_data['destination']):
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": destination
        #             }
        #         else:
        #             route_order_payload = {
        #                 "key": google_key,
        #                 "language": "ID",
        #                 "origin": origin,
        #                 "destination": waypoint_order[len(waypoint_order)]
        #             }
        #     route_order_request = requests.get(url=route_url, params=route_order_payload)
        #     route_order_json = route_order_request.json()
        #     data.append(route_order_json)

        if waypoint:
            if waypoint_order:
                route_payload = {
                    "key": google_key,
                    "language": "ID",
                    "origin": waypoint_order[len(waypoint_order)]['latlng'],
                    "destination": destination,
                    "avoid": "tolls",
                    "waypoints": "optimize:true|" + "|".join(waypoint)
                }
                route_request = requests.get(url=route_url, params=route_payload)
                route_json = route_request.json()
                order_route = route_json['routes'][0]['waypoint_order']
                last_order_route = len(waypoint_order)
                for ord in order_route:
                    last_order_route += 1
                    waypoint_order[last_order_route] = {
                        "latlng": waypoint[ord],
                        "nfc_code": waypoint_cust[ord]
                    }
                    # waypoint_order[last_order_route]['latlng'] = waypoint[ord]
                    # waypoint_order[last_order_route]['nfc_code'] = waypoint_cust[ord]
            else:
                route_payload = {
                    "key": google_key,
                    "language": "ID",
                    "origin": origin,
                    "destination": destination,
                    "avoid": "tolls",
                    "waypoints": "optimize:true|" + "|".join(waypoint)
                }
                route_request = requests.get(url=route_url, params=route_payload)
                route_json = route_request.json()
                order_route = route_json['routes'][0]['waypoint_order']
                data.append(route_json)
                i = 1
                for ord in order_route:
                    customer_data = dict()
                    customer_data['order'] = i
                    customer_data['nfc_code'] = waypoint_cust[ord]
                    latlng = waypoint[ord].split(',')
                    lat = latlng[0]
                    lng = latlng[1]
                    customer_data['lat'] = lat
                    customer_data['lng'] = lng
                    customer_order.append(customer_data)
                    i += 1

        if waypoint_order:
            i = 1
            waypoint_data = []
            while i <= len(waypoint_order):
                waypoint_data.append(waypoint_order[i]['latlng'])
                customer_data = dict()
                customer_data['order'] = i
                customer_data['nfc_code'] = waypoint_order[i]['nfc_code']
                latlng = waypoint_order[i]['latlng'].split(',')
                lat = latlng[0]
                lng = latlng[1]
                customer_data['lat'] = lat
                customer_data['lng'] = lng
                customer_order.append(customer_data)
                i += 1

            if waypoint_data:
                if len(waypoint_order) == len(request_data['destination']):
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": destination,
                        "avoid": "tolls",
                        "waypoints": "|".join(waypoint_data)
                    }
                else:
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": waypoint_order[len(waypoint_order)]['latlng'],
                        "avoid": "tolls",
                        "waypoints": "|".join(waypoint_data)
                    }
            else:
                if len(waypoint_order) == len(request_data['destination']):
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": destination,
                        "avoid": "tolls",
                    }
                else:
                    route_order_payload = {
                        "key": google_key,
                        "language": "ID",
                        "origin": origin,
                        "destination": waypoint_order[len(waypoint_order)]['latlng'],
                        "avoid": "tolls",
                    }
            route_order_request = requests.get(url=route_url, params=route_order_payload)
            route_order_json = route_order_request.json()
            data.append(route_order_json)
            # print("=======DEBUG 2======")
            # print(route_order_payload)

        # print("=======DEBUG 1======")
        # print(data[0]['routes'][0]['waypoint_order'])
        # print("=======DEBUG 2======")
        # print(customer_order)
        last_dest = len(customer_order)
        data_dest = {
            "order": last_dest,
            "lat": dest['lat'],
            "lng": dest['lng'],
            "nfc_code": request_data['end_route_id']
        }
        customer_order.append(data_dest)
        data.append(customer_order)
    else:
        # array[0]
        list_route = []
        data_routes = dict()
        data.append(data_routes)

        # array[1]
        # start_route
        data_routes = dict()
        start_route_branch = branch_controller.get_branches_by_id(request_data['start_route_id'])
        data_routes['lat'] = start_route_branch['lat']
        data_routes['lng'] = start_route_branch['lng']
        data_routes['nfc_code'] = start_route_branch['id']
        data_routes['order'] = 0
        list_route.append(data_routes)

        # destination
        i = 1
        if request_data['destination'] is not None:
            for rec in request_data['destination']:
                data_routes = dict()
                customer = customer_controller.get_customer_by_id(rec['customer'])
                data_routes['lat'] = customer['lat']
                data_routes['lng'] = customer['lng']
                data_routes['nfc_code'] = customer['code']
                data_routes['order'] = i
                list_route.append(data_routes)
                i += 1

        # end route
        data_routes = dict()
        end_route_branch = branch_controller.get_branches_by_id(request_data['end_route_id'])
        data_routes['lat'] = end_route_branch['lat']
        data_routes['lng'] = end_route_branch['lng']
        data_routes['nfc_code'] = end_route_branch['id']
        data_routes['order'] = i
        list_route.append(data_routes)
        data.append(list_route)

    response['error'] = 0
    response['data'] = data
    return jsonify(response)
