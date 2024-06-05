import re
import json
import pandas as pd

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import EmployeeModel, ApprovalModel

__author__ = 'Junior'


class EmployeeController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.employee_model = EmployeeModel()
        self.approval_model = ApprovalModel()

    def create(self, employee_data: 'dict', user_id: 'int'):
        """
        Function for create new employee

        :param employee_data: dict
        :param user_id: int
        :return:
            Employee Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.employee_model.insert_into_db(self.cursor, name=employee_data['name'],
                                                        nip=employee_data['nip'], email=employee_data['email'],
                                                        phone=employee_data['phone'], create_date=today, update_date=today,
                                                        job_function=employee_data['job_function'],
                                                        is_supervisor_sales=employee_data['is_supervisor_sales'],
                                                        is_supervisor_logistic=employee_data['is_supervisor_logistic'],
                                                        is_collector_only=employee_data['is_collector_only'],
                                                        is_can_collect=employee_data['is_can_collect'],
                                                        is_approval=employee_data['is_approval'],
                                                        approval_by=employee_data['approval_by'], create_by=user_id)
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def import_employee(self, file, user_id: 'int'):
        """
        import sales payment
        :param file: file
        :param user_id: int
        :return:
        """
        batch_data = []
        headers = ['NIP', 'Name', 'Email', 'Phone', 'Job', 'Supervisor Sales', 'Supervisor Logistic']
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])

        # TODO: Get Parent Sales Order
        df_parent = df[
            ['NIP', 'Name',  'Email', 'Phone', 'Job', 'Supervisor Sales', 'Supervisor Logistic']
        ]

        df_parent.set_index("NIP", inplace=True)
        df_parent = df_parent.groupby("NIP").last()
        df_parent.columns = ['name', 'email', 'phone', 'job_function', 'is_supervisor_sales', 'is_supervisor_logistic']
        df_parent.index.names = ['nip']

        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        for key, val in df_parent_json.items():
            value = val
            value['nip'] = key

            value['create_date'] = today
            value['update_date'] = today
            # value['import_by'] = user_id
            value['create_by'] = user_id
            value['approval_by'] = user_id
            value['is_approval'] = True
            value['is_deleted'] = False
            value['is_delete_count'] = 0
            batch_data.append(value)

        for rec in batch_data:
            try:
                result = self.employee_model.import_insert(self.cursor, rec, 'nip, is_deleted, is_delete_count')
                mysql.connection.commit()
            except Exception as e:
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def import_employee_file(self, filename: str, filename_origin: str, table: str, user_id: int):
        """

        :param filename:
        :param filename_origin:
        :param table:
        :param user_id:
        :return:
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")
        try:
            result = self.employee_model.import_insert_file(self.cursor, file_name=filename,
                                                            file_name_origin=filename_origin, table=table,
                                                            create_date=today, update_date=today, create_by=user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def check_employee_by_name(self, name: str, _id: int):
        """
        Check for name employee

        :param name: str
        :param _id: int
        :return:
            Employee Object
        """
        employee = self.employee_model.get_employee_by_name(self.cursor, name, _id)

        if len(employee) == 0:
            return False
        else:
            return True

    def get_employee_by_id(self, _id: int):
        """
        Get Employee Information Data

        :param _id: int
        :return:
            Employee Object
        """
        user_group = self.employee_model.get_employee_by_id(self.cursor, _id)

        if len(user_group) == 0:
            raise BadRequest("This Employee not exist", 200, 1, data=[])
        else:
            user_group = user_group[0]
            if user_group['edit_data'] is not None:
                user_group['edit_data'] = json.loads(user_group['edit_data'])

        return user_group

    def get_all_employee_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of Employee
        :param: page: int
        :param: limit: int
        :return:
            list Employee Object
        """
        employee = {}
        data = []
        start = page * limit - limit
        order = ''
        where = "WHERE (is_approval = 1 AND `is_deleted` = 0) "
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (name LIKE '%{0}%' OR nip LIKE '%{0}%' OR phone LIKE '%{0}%')""".format(search)
        employee_data = self.employee_model.get_all_employee(self.cursor, where=where, order=order,
                                                             start=start, limit=limit)

        count_filter = self.employee_model.get_count_all_employee(self.cursor, where=where)
        count = self.employee_model.get_count_all_employee(self.cursor, where="WHERE job_function = 'sales' ")
        if employee_data:
            for emp in employee_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                data.append(emp)
        employee['data'] = data
        employee['total'] = count
        employee['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if employee['total'] > page * limit:
            employee['has_next'] = True
        else:
            employee['has_next'] = False
        if limit <= page * count - count:
            employee['has_prev'] = True
        else:
            employee['has_prev'] = False
        return employee

    def get_all_employee_sales_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of Employee
        :param: page: int
        :param: limit: int
        :return:
            list Employee Object
        """
        employee = {}
        data = []
        start = page * limit - limit
        order = ''
        where = "WHERE (job_function = 'sales' AND is_approval = 1 AND `is_deleted` = 0) "
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (name LIKE '%{0}%' OR nip LIKE '%{0}%' OR phone LIKE '%{0}%')""".format(search)
        employee_data = self.employee_model.get_all_employee(self.cursor, where=where, order=order,
                                                             start=start, limit=limit)

        count_filter = self.employee_model.get_count_all_employee(self.cursor, where=where)
        count = self.employee_model.get_count_all_employee(self.cursor, where=where)
        if employee_data:
            for emp in employee_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                data.append(emp)
        employee['data'] = data
        employee['total'] = count
        employee['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if employee['total'] > page * limit:
            employee['has_next'] = True
        else:
            employee['has_next'] = False
        if limit <= page * count - count:
            employee['has_prev'] = True
        else:
            employee['has_prev'] = False
        return employee

    def get_all_administrator_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of Employee
        :param: page: int
        :param: limit: int
        :return:
            list Employee Object
        """
        employee = {}
        data = []
        start = page * limit - limit
        order = ''
        where = "WHERE (job_function IN ('supervisor', 'manager') AND is_approval = 1 AND `is_deleted` = 0) "
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (name LIKE '%{0}%' OR nip LIKE '%{0}%' OR phone LIKE '%{0}%')""".format(search)
        employee_data = self.employee_model.get_all_employee(self.cursor, where=where, order=order,
                                                             start=start, limit=limit)

        count_filter = self.employee_model.get_count_all_employee(self.cursor, where=where)
        count = self.employee_model.get_count_all_employee(self.cursor, where=where)
        if employee_data:
            for emp in employee_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                data.append(emp)
        employee['data'] = data
        employee['total'] = count
        employee['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if employee['total'] > page * limit:
            employee['has_next'] = True
        else:
            employee['has_next'] = False
        if limit <= page * count - count:
            employee['has_prev'] = True
        else:
            employee['has_prev'] = False
        return employee

    def get_all_logistic_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of Employee
        :param: page: int
        :param: limit: int
        :return:
            list Employee Object
        """
        employee = {}
        data = []
        start = page * limit - limit
        order = ''
        where = "WHERE (job_function IN ('driver', 'crew') AND is_approval = 1 AND `is_deleted` = 0) "
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (name LIKE '%{0}%' OR nip LIKE '%{0}%' OR phone LIKE '%{0}%')""".format(search)
        employee_data = self.employee_model.get_all_employee(self.cursor, where=where, order=order,
                                                             start=start, limit=limit)

        count_filter = self.employee_model.get_count_all_employee(self.cursor, where=where)
        count = self.employee_model.get_count_all_employee(self.cursor, where=where)
        if employee_data:
            for emp in employee_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                data.append(emp)
        employee['data'] = data
        employee['total'] = count
        employee['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if employee['total'] > page * limit:
            employee['has_next'] = True
        else:
            employee['has_next'] = False
        if limit <= page * count - count:
            employee['has_prev'] = True
        else:
            employee['has_prev'] = False
        return employee

    def update_employee(self, employee_data: 'dict', _id: 'int'):
        """
        Update Employee
        :param employee_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.employee_model.update_by_id(self.cursor, employee_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_employee_delete_count(self, nip: 'str'):
        """
        Update employee
        :param nip: str
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `nip` = '{}' AND `is_deleted` = 1".format(nip)
            order = "ORDER BY is_delete_count DESC"
            count = self.employee_model.get_all_employee(
                self.cursor, select=select, where=where, order=order, start=0, limit=1000)[0]
        except Exception as e:
            count = {
                "is_delete_count": 0
            }

        return count['is_delete_count']

    def rollback_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `employee` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_all_employee_import(self):
        """
        Get List Of import branch
        :return:
            list Sales Orders Object
        """
        import_file = {}
        data = []
        import_data = self.employee_model.get_all_employee_import(self.cursor, where="""WHERE `status` = 0 
        AND `table_name` = 'employee'""")
        count = self.employee_model.get_count_all_employee_import(self.cursor, key="id", where="""WHERE `status` = 0 
        AND `table_name` = 'employee'""")
        if import_data:
            for emp in import_data:
                data.append(emp)
        import_file['data'] = data
        import_file['total'] = count

        # TODO: Check Has Next and Prev
        import_file['has_next'] = False
        import_file['has_prev'] = False
        return import_file

    # TODO: using for general purpose
    def get_import_file(self, _id: int):
        """
        Get import by id

        :param _id: int
        :return:
            area Object
        """
        import_file = self.employee_model.get_import_by_id(self.cursor, _id)

        if len(import_file) == 0:
            raise BadRequest("This import file not exist", 200, 1, data=[])
        else:
            import_file = import_file[0]

        return import_file

    def update_import_file(self, _id: int, user_id: int):
        """
        Get area Information Data

        :param _id: int
        :param user_id: int
        :return:
            area Object
        """
        try:
            result = self.employee_model.update_import_by_id(self.cursor, _id, user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result