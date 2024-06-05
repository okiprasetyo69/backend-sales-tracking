import re
import json

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import InboxModel, UserModel, BranchesModel, EmployeeModel, DivisionModel

__author__ = 'Junior'


class InboxController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.inbox_model = InboxModel()
        self.user_model = UserModel()
        self.branch_model = BranchesModel()
        self.division_model = DivisionModel()
        self.employee_model = EmployeeModel()

    def create(self, create_data: 'dict'):
        """
        Function for create new log activity

        :param create_data: dict
        :return:
            Success or failure message
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.inbox_model.insert_into_db(
                self.cursor, title=create_data['title'], date=today, message=create_data['message'],
                payload=create_data['payload'], category=create_data['category'], user_id=create_data['user_id'],
                from_id=create_data['from_id'], create_date=today, update_date=today
            )
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def get_all_inbox_data(
            self, page: int, limit: int, search: str, column: str, direction: str, tipe: 'str', user_id: 'int'
    ):
        """
        Get List Of division
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :param: tipe: str
        :param: user_id: int
        :return:
            list division Object
        """
        result = {}
        data = []
        start = page * limit - limit
        order = ''
        where = 'WHERE `user_id` = {} '.format(user_id)
        where_original = where
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (title LIKE '%{0}%' OR category LIKE '%{0}%' OR message LIKE '%{0}%')""".format(search)

        inbox_data = self.inbox_model.get_all_inbox(
            self.cursor, where=where, order=order, start=start, limit=limit
        )
        count_filter = self.inbox_model.get_count_all_inbox(
            self.cursor, where=where
        )
        count = self.inbox_model.get_count_all_inbox(
            self.cursor, where=where_original
        )

        if inbox_data:
            for emp in inbox_data:
                if emp['payload'] is not None:
                    emp['payload'] = json.loads(emp['payload'])
                if emp['from_id'] is not None:
                    try:
                        emp['from'] = self.user_model.get_user_by_id(
                            self.cursor, emp['from_id'],
                            select="username, employee_id, branch_id, division_id"
                        )[0]
                        if emp['from']['employee_id'] is not None:
                            try:
                                employee = self.employee_model.get_employee_by_id(
                                    self.cursor, emp['from']['employee_id'], select="""name, job_function"""
                                )[0]
                                emp['from']['name'] = employee['name']
                                emp['from']['job_function'] = employee['job_function']
                            except:
                                emp['from']['name'] = None
                        if emp['from']['branch_id'] is not None:
                            try:
                                emp['from']['branch_name'] = self.branch_model.get_branches_by_id(
                                    self.cursor, emp['from']['branch_id'], select="""name""")[0]['name']
                            except:
                                emp['from']['branch_name'] = None
                        if emp['from']['division_id'] is not None:
                            try:
                                emp['from']['division_name'] = self.division_model.get_division_by_id(
                                    self.cursor, emp['from']['division_id'], select="division_name")[0][
                                    'division_name']
                            except:
                                emp['from']['division_name'] = None
                        else:
                            emp['from']['division_name'] = None
                    except:
                        emp['from'] = {}
                else:
                    emp['from'] = {}
                data.append(emp)

        result['data'] = data
        result['total'] = count
        result['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if result['total'] > page * limit:
            result['has_next'] = True
        else:
            result['has_next'] = False
        if limit <= page * count - count:
            result['has_prev'] = True
        else:
            result['has_prev'] = False

        return result