import os
import json

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity

from rest.controllers import ApprovalController
from rest.exceptions import BadRequest
from rest.helpers import Validator

__author__ = 'junior'

bp = Blueprint(__name__, "approval")


@bp.route('/approval/notif/checker', methods=["GET"])
@jwt_required()
def check_notif_approval():
    """
    list all Inbox
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/inbox?page=1&limit=50"
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
    approval_controller = ApprovalController()

    branch_privilege = current_identity.branch_privilege
    division_privilege = current_identity.division_privilege

    response = {
        'error': 1,
        'message': '',
        'data': [],
        'total': 0
    }
    data = []
    total = 0
    # TODO: for area
    prefix = 'area'
    create = False
    edit = False
    delete = False
    setting = current_identity.permissions['setting']['data']['setting-config']['data']['setting-config-area']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['setting']['data']['setting-config']['data'][
                'setting-config-area']
            permission[3] = setting_group['rule'][3]
        else:
            permission[3] = 0
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_area = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_area:
        data.append({
            'prefix': prefix,
            'count': count_area
        })
        total += count_area

    # TODO: for assets
    prefix = 'assets'
    create = False
    edit = False
    delete = False
    setting = current_identity.permissions['assets']['data']['assets-data']['data']['assets-data-assets']
    permission = setting['rule']

    if permission[1] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[1] = setting_group['rule'][1]
        else:
            permission[1] = 0
    if permission[2] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[2] = setting_group['rule'][2]
        else:
            permission[2] = 0
    if permission[3] == 10:
        if current_identity.permissions_group is not None:
            setting_group = current_identity.permissions_group['assets']['data']['assets-data']['data'][
                'assets-data-assets']
            permission[3] = setting_group['rule'][3]
        else:
            permission[3] = 0
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_assets = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_assets:
        data.append({
            'prefix': prefix,
            'count': count_assets
        })
        total += count_assets

    # TODO: for branch
    prefix = 'branches'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_branch = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_branch:
        data.append({
            'prefix': prefix,
            'count': count_branch
        })
        total += count_branch

    # TODO: for customer
    prefix = 'customer'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_customer = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_customer:
        data.append({
            'prefix': prefix,
            'count': count_customer
        })
        total += count_customer

    # TODO: for users
    prefix = 'user'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_user = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_user:
        data.append({
            'prefix': prefix,
            'count': count_user
        })
        total += count_user

    # TODO: for users/groups
    prefix = 'user/groups'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_user_group = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_user_group:
        data.append({
            'prefix': prefix,
            'count': count_user_group
        })
        total += count_user_group

    # TODO: for division
    prefix = 'division'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_division = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_division:
        data.append({
            'prefix': prefix,
            'count': count_division
        })
        total += count_division

    # TODO: for employee sales
    prefix = 'employee/sales'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_sales = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_sales:
        data.append({
            'prefix': prefix,
            'count': count_sales
        })
        total += count_sales

    # TODO: for employee logistic
    prefix = 'employee/logistic'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_logistic = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_logistic:
        data.append({
            'prefix': prefix,
            'count': count_logistic
        })
        total += count_logistic

    # TODO: for employee supervisor
    prefix = 'employee/supervisor'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_supervisor = approval_controller.get_count_approval(prefix=prefix, create=create, edit=edit, delete=delete)
    if count_supervisor:
        data.append({
            'prefix': prefix,
            'count': count_supervisor
        })
        total += count_supervisor

    # TODO: for visit/cycle
    prefix = 'visit/cycle'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_visit_cycle = approval_controller.get_count_approval_privilege(
        prefix=prefix, create=create, edit=edit, delete=delete, branch_privilege=branch_privilege,
        division_privilege=division_privilege
    )
    if count_visit_cycle:
        data.append({
            'prefix': prefix,
            'count': count_visit_cycle
        })
        total += count_visit_cycle

    # TODO: for visit/plan
    prefix = 'visit/plan'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_visit_plan = approval_controller.get_count_approval_privilege(
        prefix=prefix, create=create, edit=edit, delete=delete, branch_privilege=branch_privilege,
        division_privilege=division_privilege
    )
    if count_visit_plan:
        data.append({
            'prefix': prefix,
            'count': count_visit_plan
        })
        total += count_visit_plan

    # TODO: for delivery/cycle
    prefix = 'delivery/cycle'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_delivery_cycle = approval_controller.get_count_approval_privilege(
        prefix=prefix, create=create, edit=edit, delete=delete, branch_privilege=branch_privilege,
        division_privilege=None
    )
    if count_delivery_cycle:
        data.append({
            'prefix': prefix,
            'count': count_delivery_cycle
        })
        total += count_delivery_cycle

    # TODO: for delivery/plan
    prefix = 'delivery/plan'
    create = False
    edit = False
    delete = False
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
    if permission[1] == 3:
        create = True
    if permission[2] == 3:
        edit = True
    if permission[3] == 3:
        delete = True

    count_delivery_plan = approval_controller.get_count_approval_privilege(
        prefix=prefix, create=create, edit=edit, delete=delete, branch_privilege=branch_privilege,
        division_privilege=None
    )
    if count_delivery_plan:
        data.append({
            'prefix': prefix,
            'count': count_delivery_plan
        })
        total += count_delivery_plan

    response['error'] = 0
    response['data'] = data
    response['total'] = total

    return jsonify(response)


@bp.route('/approval/<approval_id>', methods=["GET"])
@jwt_required()
def get_approval_by_id(approval_id):
    """
    list all Inbox
    :example:
        curl -i -x GET
        -H "Authorization:JWT <token>"
        "http://localhost:7091/inbox?page=1&limit=50"
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
    approval_controller = ApprovalController()

    response = {
        'error': 1,
        'message': '',
        'data': []
    }

    result = approval_controller.get_approval_by_id(approval_id)

    response['error'] = 0
    response['data'] = result

    return jsonify(response)