import re
import json

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import CompanyModel, GeneralModel, NotifModel

__author__ = 'Junior'


class SettingController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.company_model = CompanyModel()
        self.general_model = GeneralModel()
        self.notif_model = NotifModel()

    # TODO: For controller setting company
    def get_company_by_id(self, _id: int):
        """
        Get company Information Data

        :param _id: int
        :return:
            company Object
        """
        company = self.company_model.get_company_by_id(self.cursor, _id)
        if len(company) == 0:
            raise BadRequest("This Company not exist", 200, 1, data=[])
        else:
            company = company[0]
            if company['edit_data'] is not None:
                company['edit_data'] = json.loads(company['edit_data'])
            if company['working_hour_start'] is not None:
                company['working_hour_start'] = str(company['working_hour_start'])
                company['working_hour_start'] = company['working_hour_start'].split(':')
                company['working_hour_start'] = company['working_hour_start'][0]+':'+company['working_hour_start'][1]
            if company['working_hour_end'] is not None:
                company['working_hour_end'] = str(company['working_hour_end'])
                company['working_hour_end'] = company['working_hour_end'].split(':')
                company['working_hour_end'] = company['working_hour_end'][0]+':'+company['working_hour_end'][1]
            # if company['division_id'] is not None:
            #     company['division_id'] = json.loads(company['division_id'])


        return company

    def update_company(self, company_data: 'dict', _id: 'int'):
        """
        Update Company
        :param company_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.company_model.update_by_id(self.cursor, company_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    # TODO: for controller setting general
    def get_general_by_id(self, _id: int):
        """
        Get company Information Data

        :param _id: int
        :return:
            company Object
        """
        general = self.general_model.get_general_by_id(self.cursor, _id)
        if len(general) == 0:
            raise BadRequest("This Company not exist", 200, 1, data=[])
        else:
            general = general[0]
            if general['visit_cycle_start'] is not None:
                general['visit_cycle_start'] = str(general['visit_cycle_start'])
            # if general['working_hour_start'] is not None:
            #     general['working_hour_start'] = str(general['working_hour_end'])
            # if general['working_hour_end'] is not None:
            #     general['working_hour_end'] = str(general['working_hour_end'])

        return general

    def update_general(self, general_data: 'dict', _id: 'int'):
        """
        Update Setting General
        :param general_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.general_model.update_by_id(self.cursor, general_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    # TODO: for controller setting notifications
    def get_all_notif_data(self, type: str):
        """
        Get notifications setting Data

        :param type: str
        :return:
            Notifications Object
        """
        notif = {}
        data = []
        notif_data = self.notif_model.get_all_notif_by_type(self.cursor, type)
        if notif_data:
            data = notif_data
        notif['has_prev'] = False
        notif['has_next'] = False
        notif['data'] = data
        notif['total'] = len(data)
        return notif

    def get_notif_by_id(self, _id: int):
        """
        Get notifications Data

        :param _id: int
        :return:
            company Object
        """
        notif = self.notif_model.get_notif_by_id(self.cursor, _id)
        if len(notif) == 0:
            raise BadRequest("This Notif not exist", 200, 1, data=[])
        else:
            notif = notif[0]
            # if general['edit_data'] is not None:
            #     general['edit_data'] = json.loads(general['edit_data'])
            # if general['working_hour_start'] is not None:
            #     general['working_hour_start'] = str(general['working_hour_end'])
            # if general['working_hour_end'] is not None:
            #     general['working_hour_end'] = str(general['working_hour_end'])

        return notif

    def update_notif(self, notif_data: 'dict', _id: 'int'):
        """
        Update Setting General
        :param notif_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.notif_model.update_by_id(self.cursor, notif_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_print_unique_code(self):
        """
        Get Unique code for print
        :return:
            Message Boolean Success or Failure
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d")
        today = "{} 01:00:00".format(today)

        format_day = datetime.strptime(today, "%Y-%m-%d %H:%M:%S")
        integer_day = int(format_day.timestamp())
        integer_weekday = format_day.weekday()
        result = int("{0}{1}".format(integer_day, integer_weekday))

        return result

    def check_print_unique_code(self, check_data: dict):
        """
        Get Unique code for print
        :param check_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        date_day = "{} 01:00:00".format(check_data['date'])

        format_day = datetime.strptime(date_day, "%Y-%m-%d %H:%M:%S")
        integer_day = int(format_day.timestamp())
        integer_weekday = format_day.weekday()
        checker_day = int("{0}{1}".format(integer_day, integer_weekday))

        checker_code = int(check_data['code'])
        if checker_code == checker_day:
            return True
        else:
            return False
