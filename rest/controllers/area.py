import re
import json

from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import current_app, render_template

from rest.exceptions import BadRequest, RestException
from rest.helpers import mysql
from rest.models import AreaModel

__author__ = 'Junior'


class AreaController(object):
    def __init__(self):
        self.cursor = mysql.connection.cursor()
        self.area_model = AreaModel()

    def create(self, area_data: 'dict', user_id: 'int'):
        """
        Function for create new area

        :param area_data: dict
        :param user_id: int
        :return:
            area Object
        """
        today = datetime.today()
        today = today.strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = self.area_model.insert_into_db(self.cursor, name=area_data['name'],
                                                    marker_type=area_data['marker_type'],
                                                    marker_color=area_data['marker_color'],
                                                    markers=area_data['markers'],
                                                    description=area_data['description'],
                                                    create_date=today, update_date=today,
                                                    is_approval=area_data['is_approval'],
                                                    approval_by=area_data['approval_by'], create_by=user_id)
            mysql.connection.commit()
            last_insert_id = self.cursor.lastrowid
        except Exception as e:
            raise BadRequest(e, 200, 1, data=[])

        return last_insert_id

    def check_area_by_name(self, name: str, _id: int):
        """
        Check for name area

        :param name: str
        :param _id: int
        :return:
            area Object
        """
        area = self.area_model.get_area_by_name(self.cursor, name, _id)

        if len(area) == 0:
            return False
        else:
            return True

    def get_area_by_id(self, _id: int):
        """
        Get area Information Data

        :param _id: int
        :return:
            area Object
        """
        area = self.area_model.get_area_by_id(self.cursor, _id)

        if len(area) == 0:
            raise BadRequest("This area not exist", 500, 1, data=[])
        else:
            area = area[0]
            if area['edit_data'] is not None:
                area['edit_data'] = json.loads(area['edit_data'])
            if area['markers'] is not None:
                area['markers'] = json.loads(area['markers'])

        return area

    def get_all_area_data(self, page: int, limit: int, search: str, column: str, direction: str):
        """
        Get List Of area
        :param: page: int
        :param: limit: int
        :param: search: str
        :param: column: str
        :param: direction: str
        :return:
            list area Object
        """
        area = {}
        data = []
        start = page * limit - limit
        order = ''
        where = "WHERE (`is_approval` = 1 AND `is_deleted` = 0) "
        if column:
            order = """ORDER BY {0} {1}""".format(column, direction)
        if search:
            where += """AND (name LIKE '%{0}%' OR description LIKE '%{0}%') """.format(search)
        area_data = self.area_model.get_all_area(self.cursor, where=where, order=order, start=start, limit=limit)
        count_filter = self.area_model.get_count_all_area(self.cursor, where=where)
        count = self.area_model.get_count_all_area(self.cursor)
        if area_data:
            for emp in area_data:
                if emp['edit_data'] is not None:
                    emp['edit_data'] = json.loads(emp['edit_data'])
                if emp['markers'] is not None:
                    emp['markers'] = json.loads(emp['markers'])
                data.append(emp)
        area['data'] = data
        area['total'] = count
        area['total_filter'] = count_filter

        # TODO: Check Has Next and Prev
        if area['total'] > page * limit:
            area['has_next'] = True
        else:
            area['has_next'] = False
        if limit <= page * count - count:
            area['has_prev'] = True
        else:
            area['has_prev'] = False
        return area

    def update_area(self, area_data: 'dict', _id: 'int'):
        """
        Update area
        :param area_data: dict
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            result = self.area_model.update_by_id(self.cursor, area_data)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result

    def rollback_insert(self, _id: 'int'):
        """
        Rollback insert branches
        :param _id: int
        :return:
            Message Boolean Success or Failure
        """
        try:
            query = "DELETE from `area` WHERE id = {}".format(_id)
            result = self.cursor.execute(query=query)
            mysql.connection.commit()
        except Exception as e:
            raise BadRequest(e, 200, 1)

        return result