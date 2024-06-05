import re

from flask import Blueprint, jsonify, request, current_app
from flask_jwt import jwt_required, current_identity

from rest.helpers import USERS_NOTIF
from rest.exceptions import BadRequest

bp = Blueprint(__name__, "menu")


@bp.route('/menu', methods=["GET"])
@jwt_required()
def get_menu():
    """
    Get Menu with permissions
    :example:
        curl -i -x GET
        -H "Authorization: JWT <token>"
        "http://localhost:7091/menu"
    :endpoint:
        GET /menu
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "",
            "data": Menu Object
        }
    """
    parent = None
    child = None
    selected = None
    if request.args.get('selected'):
        selected = request.args.get('selected')
        parsing_str = selected.split('-')
        parent = parsing_str[0]
        if len(parsing_str) > 1:
            child = parsing_str[0]+'-'+parsing_str[1]
        else:
            child = ''

    result_menu = dict()
    result_menu['menu'] = []
    menu = current_app.config['MENU_CONFIGURATION']

    if current_identity.permissions is not None:
        for m in menu['menu']:
            if m.get('link'):
                if selected:
                    if m['code'] == selected:
                        m['selected'] = True
                    else:
                        if m.get('selected'):
                            del m['selected']
                else:
                    if m.get('selected'):
                        del m['selected']
                if parent:
                    if m['code'] == parent:
                        m['expanded'] = True
                    else:
                        if m.get('expanded'):
                            del m['expanded']
                else:
                    if m.get('expanded'):
                        del m['expanded']
                if current_identity.permissions_group is not None:
                    if current_identity.permissions[m['code']]['rule-view'] == 10:
                        if current_identity.permissions_group[m['code']]['rule-view'] == 0:
                            m['hidden'] = True
                        else:
                            if m.get('hidden'):
                                del m['hidden']
                    else:
                        if current_identity.permissions[m['code']]['rule-view'] == 0:
                            m['hidden'] = True
                        else:
                            if m.get('hidden'):
                                del m['hidden']
                else:
                    if current_identity.permissions[m['code']]['rule-view'] == 0 or current_identity.permissions[m['code']]['rule-view'] == 10:
                        m['hidden'] = True
                    else:
                        if m.get('hidden'):
                            del m['hidden']
                child_menu = []
                if m.get('children'):
                    for mn in m['children']:
                        if selected:
                            if mn['code'] == selected:
                                mn['selected'] = True
                            else:
                                if mn.get('selected'):
                                    del mn['selected']
                        else:
                            if mn.get('selected'):
                                del mn['selected']
                        if child:
                            if mn['code'] == child:
                                mn['expanded'] = True
                            else:
                                if mn.get('expanded'):
                                    del mn['expanded']
                        else:
                            if mn.get('expanded'):
                                del mn['expanded']
                        if current_identity.permissions_group is not None:
                            if current_identity.permissions[m['code']]['data'][mn['code']]['rule-view'] == 10:
                                if current_identity.permissions_group[m['code']]['data'][mn['code']]['rule-view'] == 0:
                                    mn['hidden'] = True
                                else:
                                    if mn.get('hidden'):
                                        del mn['hidden']
                            else:
                                if current_identity.permissions[m['code']]['data'][mn['code']]['rule-view'] == 0:
                                    mn['hidden'] = True
                                else:
                                    if mn.get('hidden'):
                                        del mn['hidden']
                        else:
                            if current_identity.permissions[m['code']]['data'][mn['code']]['rule-view'] == 0 \
                                    or current_identity.permissions[m['code']]['data'][mn['code']]['rule-view'] == 10:
                                mn['hidden'] = True
                            else:
                                if mn.get('hidden'):
                                    del mn['hidden']
                        second_child_menu = []
                        if mn.get('children'):
                            for mne in mn['children']:
                                if selected:
                                    if mne['code'] == selected:
                                        mne['selected'] = True
                                    else:
                                        if mne.get('selected'):
                                            del mne['selected']
                                else:
                                    if mne.get('selected'):
                                        del mne['selected']
                                if current_identity.permissions_group is not None:
                                    if current_identity.permissions[m['code']]['data'][mn['code']]['data'][mne['code']]['rule-view'] == 10:
                                        if current_identity.permissions_group[m['code']]['data'][mn['code']]['data'][mne['code']]['rule-view'] == 0:
                                            mne['hidden'] = True
                                        else:
                                            if mne.get('hidden'):
                                                del mne['hidden']
                                    else:
                                        if current_identity.permissions[m['code']]['data'][mn['code']]['data'][mne['code']]['rule-view'] == 0:
                                            mne['hidden'] = True
                                        else:
                                            if mne.get('hidden'):
                                                del mne['hidden']
                                else:
                                    if current_identity.permissions[m['code']]['data'][mn['code']]['data'][mne['code']]['rule-view'] == 0 or \
                                                    current_identity.permissions[m['code']]['data'][mn['code']]['data'][mne['code']]['rule-view'] == 10:
                                        mne['hidden'] = True
                                    else:
                                        if mne.get('hidden'):
                                            del mne['hidden']
                                second_child_menu.append(mne)
                            mn['children'] = second_child_menu
                        child_menu.append(mn)
                    m['children'] = child_menu
            result_menu['menu'].append(m)

    response = {
        'error': 0,
        'message': "success",
        'data': result_menu
    }

    return jsonify(response)


@bp.route('/menu/access_rule', methods=["GET"])
@jwt_required()
def get_access_rule():
    """
    Get Permission rule for each menu
    :example:
        curl -i -x GET
        -H "Authorization: JWT <token>"
        "http://localhost:7091/menu?code=<string>"
    :param:
        code: string
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "",
            "data": Permission Object
        }
    """
    menu_code = request.args.get('code')
    permission = []
    rule_view = 0
    for rec in current_identity.permissions:
        if rec == menu_code:
            rule_view = current_identity.permissions[rec]['rule-view']
            if current_identity.permissions_group:
                if rule_view == 10:
                    rule_view = current_identity.permissions_group[rec]['rule-view']
            else:
                if rule_view == 10:
                    rule_view = 0
        if current_identity.permissions[rec].get('data'):
            for rc in current_identity.permissions[rec]['data']:
                if rc == menu_code:
                    rule_view = current_identity.permissions[rec]['data'][rc]['rule-view']
                    if current_identity.permissions_group:
                        if rule_view == 10:
                            rule_view = current_identity.permissions_group[rec]['data'][rc]['rule-view']
                    else:
                        if rule_view == 10:
                            rule_view = 0
                if current_identity.permissions[rec]['data'][rc].get('data'):
                    for r in current_identity.permissions[rec]['data'][rc]['data']:
                        if r == menu_code:
                            if current_identity.permissions[rec]['data'][rc]['data'][r].get('rule'):
                                permission = current_identity.permissions[rec]['data'][rc]['data'][r]['rule']
                                if current_identity.permissions_group:
                                    if permission[0] == 10:
                                        permission[0] = current_identity.permissions_group[rec]['data'][rc]['data'][r]['rule'][0]
                                    if permission[1] == 10:
                                        permission[1] = current_identity.permissions_group[rec]['data'][rc]['data'][r]['rule'][1]
                                    if permission[2] == 10:
                                        permission[2] = current_identity.permissions_group[rec]['data'][rc]['data'][r]['rule'][2]
                                    if permission[3] == 10:
                                        permission[3] = current_identity.permissions_group[rec]['data'][rc]['data'][r]['rule'][3]
                                    if permission[4] == 10:
                                        permission[4] = current_identity.permissions_group[rec]['data'][rc]['data'][r]['rule'][4]
                                    if permission[5] == 10:
                                        permission[5] = current_identity.permissions_group[rec]['data'][rc]['data'][r]['rule'][5]
                                else:
                                    if permission[0] == 10:
                                        permission[0] = 0
                                    if permission[1] == 10:
                                        permission[1] = 0
                                    if permission[2] == 10:
                                        permission[2] = 0
                                    if permission[3] == 10:
                                        permission[3] = 0
                                    if permission[4] == 10:
                                        permission[4] = 0
                                    if permission[5] == 10:
                                        permission[5] = 0
                                rule_view = current_identity.permissions[rec]['data'][rc]['data'][r]['rule-view']
                                if current_identity.permissions_group:
                                    if rule_view == 10:
                                        rule_view = current_identity.permissions_group[rec]['data'][rc]['data'][r]['rule-view']
                                else:
                                    if rule_view == 10:
                                        rule_view = 0
                                break
    refine_permissions = dict()
    if permission:
        refine_permissions = {
            'view': permission[0],
            'create': permission[1],
            'edit': permission[2],
            'delete': permission[3],
            'import': permission[4],
            'print': permission[5],
            'index': rule_view
        }
    else:
        refine_permissions = {
            'index': rule_view
        }
    response = {
        'error': 0,
        'message': "success",
        'data': refine_permissions
    }

    return jsonify(response)


@bp.route('/permission/<category>', methods=["GET"])
@jwt_required()
def get_permission_list(category):
    """
    Get Permission rule for each menu
    :example:
        curl -i -x GET
        -H "Authorization: JWT <token>"
        "http://localhost:7091/menu?code=<string>"
    :param:
        code: string
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "",
            "data": Permission Object
        }
    """
    if category == 'user':
        permission = current_app.config['PERMISSION_CONFIGURATION']
    elif category == 'user_group':
        permission = current_app.config['PERMISSION_GROUP_CONFIGURATION']
    else:
        raise BadRequest("wrong type", 500, 1, data=[])

    response = {
        'error': 0,
        'message': "success",
        'data': permission
    }

    return jsonify(response)


@bp.route('/test/menu/notif', methods=["GET"])
def test_notif_menu_nodejs():
    """
    :example:
        curl -i -x PUT
        -H "Authorization:JWT <token>"
        "http://localhost:7091/generate"
    :return:
        HTTP/1.1 200 OK
        Content-Type: text/javascript
        {
            "error": 0,
            "message": "success generate"
        }
    """
    response = {
        'error': 0,
        'message': 'sucess test emit',
        'data': USERS_NOTIF
    }
    return jsonify(response)