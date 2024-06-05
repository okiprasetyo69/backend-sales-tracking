import re
import json
import pandas as pd

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import DivisionModel, ApprovalModel

__author__ = 'Junior'


class DivisionController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.division_model = DivisionModel()
        self.approval_model = ApprovalModel()

    def create(self, division_data: 'dict', user_id: 'int'):
        """
        Function for create new division

        :param division_data: dict
        :param user_id: int
        :return:
            Division Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.division_model.insert_into_db(self.cursor, division_code=division_data['division_code'],
                                                        division_name=division_data['division_name'],
                                                        create_date=today, update_date=today,
                                                        is_approval=division_data['is_approval'],
                                                        approval_by=division_data['approval_by'], create_by=user_id)
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def import_division(self, file, user_id: 'int'):
        """
        import division
        :param file: file
        :param user_id: int
        :return:
        """
        headers = ['Division Code', 'Name']
        batch_data = []
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        df = pd.read_excel(file, sheet_name=0, skiprows=0)
        for idx in df.columns:
            if idx not in headers:
                raise BadRequest('Wrong header name', 422, 1, data=[{'header': idx}])

        # TODO: Get Parent Sales Order
        df_parent = df[
            ['Division Code', 'Name']
        ]
        df_parent.set_index("Division Code", inplace=True)
        df_parent = df_parent.groupby('Division Code').last()
        df_parent.columns = ['division_name']
        df_parent.index.names = ['division_code']

        df_parent_json = df_parent.to_json(orient='index', date_format='iso')
        df_parent_json = json.loads(df_parent_json)

        for key, val in df_parent_json.items():
            value = val
            value['division_code'] = key[:2]
            value['create_date'] = today
            value['update_date'] = today
            # value['import_by'] = user_id
            value['create_by'] = user_id
            value['approval_by'] = user_id
            value['is_approval'] = True
            batch_data.append(value)

        for rec in batch_data:
            try:
                result = self.division_model.import_insert(self.cursor, rec, 'division_code')
                mysql.connection.commit()
            except Exception as e:
                # raise BadRequest(e, 200, 1, data=[])
                pass

        return True

    def import_division_file(self, filename: str, filename_origin: str, table: str, user_id: int):
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
            result = self.division_model.import_insert_file(self.cursor, file_name=filename,
                                                            file_name_origin=filename_origin, table=table,
                                                            create_date=today, update_date=today, create_by=user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return result

    def check_division_by_name(self, name: str, _id: int):
        """
        Check for name division

        :param name: str
        :param _id: int
        :return:
            division Object
        """
        division = self.division_model.get_division_by_name(self.cursor, name, _id)

        if len(division) == 0:
            return False
        else:
            return True

    def check_division_by_code(self, code: str, _id: int):
        """
        Check for name division

        :param name: str
        :param _id: int
        :return:
            division Object
        """
        division = self.division_model.get_division_by_code(self.cursor, code, _id)

        if len(division) == 0:
            return False
        else:
            return True

    def get_division_by_id(self, _id: int):
        """
        Get division Information Data

        :param _id: int
        :return:
            division Object
        """
        division = self.division_model.get_division_by_id(self.cursor, _id)

        if len(division) == 0:
            raise BadRequest("This division not exist", 500, 1, data=[])
        else:
            division = division[0]
            if division['edit_data'] is not None:
                division['edit_data'] = json.loads(division['edit_data'])

        return division

    def get_all_division_data(
            self, page: int, limit: int, search: str, column: str, direction: str, dropdown: bool,
            division_privilege: list
    ):
        """
        Get List Of division
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list division Object
        """
        division = {}
        data = []
        start = page * limit - limit
        order = ''
        where = """WHERE (is_approval = 1 AND is_deleted = 0) """
        if dropdown:
            where += "AND id IN ({0}) ".format(
                ", ".join(str(x) for x in division_privilege)
            )
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (division_name LIKE '%{0}%' OR division_code LIKE '%{0}%')""".format(search)
        division_data = self.division_model.get_all_division(self.cursor, where=where, order=order,
                                                             start=start, limit=limit)
        count_filter = self.division_model.get_count_all_division(self.cursor, where=where)
        count = self.division_model.get_count_all_division(self.cursor)
        if division_data:
            for emp in division_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                data.append(emp)
        division['data'] = data
        division['total'] = count
        division['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if division['total'] > page * limit:
            division['has_next'] = True
        else:
            division['has_next'] = False
        if limit <= page * count - count:
            division['has_prev'] = True
        else:
            division['has_prev'] = False
        return division

    def get_division_data_by_list(self, list_id: str):
        """
        Get List Of division
        :param: list_id: list
        :return:
            list division Object
        """
        division = {}
        data = []
        division_data = self.division_model.get_division_by_list_id(self.cursor, _id=list_id)
        count = self.division_model.get_count_by_list_id_division(self.cursor, _id=list_id)
        if division_data:
            for emp in division_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                data.append(emp)
        division['data'] = data
        division['total'] = count

        # TODO: Check Has Next and Prev
        division['has_next'] = False
        division['has_prev'] = False
        return division

    def update_division(self, division_data: 'dict', _id: 'int'):
        """
        Update division
        :param division_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.division_model.update_by_id(self.cursor, division_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_division_delete_count(self, code: 'str'):
        """
        Update division
        :param code: str
        :return:
            Message Boolean Success or Failure
        """
        try:
            select = "is_delete_count"
            where = "WHERE `division_code` = '{}' AND `is_deleted` = 1".format(code)
            order = "ORDER BY is_delete_count DESC"
            count = self.division_model.get_all_division(
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
            query = "DELETE from `divisions` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_all_division_import(self):
        """
        Get List Of import branch
        :return:
            list Sales Orders Object
        """
        import_file = {}
        data = []
        import_data = self.division_model.get_all_divsion_import(self.cursor, where="""WHERE `status` = 0 
        AND `table_name` = 'division'""")
        count = self.division_model.get_count_all_division_import(self.cursor, key="id", where="""WHERE `status` = 0 
        AND `table_name` = 'division'""")
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
        import_file = self.division_model.get_import_by_id(self.cursor, _id)

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
            result = self.division_model.update_import_by_id(self.cursor, _id, user_id)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def get_list_all_division_id(self):
        """
        Get List All Division ID
        :return:
            list id
        """
        try:
            query = "SELECT id from `divisions` "
            self.cursor.execute(query)
            division = self.cursor.fetchall()
            list_id = []
            for data in division:
                list_id.append(data['id'])
        except Exception as e:
            raise BadRequest(e, 422, 1)

        return list_id