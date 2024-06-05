import json
from flask import Blueprint, jsonify

__author__ = 'Rendy Ichtiar Saputra'

bp = Blueprint(__name__, "wso")


@bp.route('/wso/packages', methods=["GET"])
def package():
    response = {
        'error': 0,
        'message': '',
        'data': {
            'packages': [
                'id.co.beton.management_trackingsystem',
                'id.co.beton.saleslogistic_trackingsystem',
                'com.whatsapp',
                'com.google.android.dialer',
                'com.theappninjas.gpsjoystick',
                'com.google.android.apps.docs'
            ]
        }
    }

    return jsonify(response)


@bp.route('/wso/pin', methods=["GET"])
def pin():
    response = {
        'error': 0,
        'message': '',
        'data': {
            'pin': '1234'
        }
    }

    return jsonify(response)
