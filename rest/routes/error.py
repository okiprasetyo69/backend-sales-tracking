import logging

from flask import Blueprint, jsonify
from rest.exceptions import RestException

__author__ = 'junior'

bp = Blueprint(__name__, "error")
log = logging.getLogger(__name__)


@bp.app_errorhandler(RestException)
def handle_rest_exception(e):
    """
    This error will show if RestException raised
    """

    log.warning(e)
    response = e.to_dict()
    return jsonify(response), e.status_code


@bp.app_errorhandler(404)
def page_not_found(e):
    """
    Page Not Found
    """
    log.warning(e)
    response = {
        "message": "Resource update 20200314"
    }
    return jsonify(response), 404


@bp.app_errorhandler(500)
def server_error(e):
    """
    This error will show if error un handle
    """
    log.error(e)
    response = {
        "message": "Internal server error"
    }
    return jsonify(response), 500