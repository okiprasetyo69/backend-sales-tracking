from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, JSON, FLOAT, ForeignKey
from sqlalchemy.orm import relationship

from rest.configuration import Base, session
from rest.models.orm.employee import EmployeeModel
from rest.models.orm.divisions import DivisionModel
from rest.models.orm.user import UserModel
from rest.models.orm.customer import CustomerModel
from rest.models.orm.branches import BranchesModel


class SalesActivityModel(Base):
    __tablename__ = 'sales_activity'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    visit_plan_id = Column(BigInteger, ForeignKey("visit_plan.id"))
    nfc_code = Column(VARCHAR)
    tap_nfc_date = Column(TIMESTAMP)
    tap_nfc_type = Column(VARCHAR)
    route_breadcrumb = Column(JSON)
    distance = Column(FLOAT)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    user = relationship("UserModel", foreign_keys=[user_id])
    visit_plan = relationship("VisitPlanModel", foreign_keys=[visit_plan_id])

    def is_tap_start(self):
        return self.tap_nfc_type is "START"

    def is_tap_stop(self):
        return self.tap_nfc_type is "STOP"

    def is_tap_in(self):
        return self.tap_nfc_type is "IN"

    def is_tap_out(self):
        return self.tap_nfc_type is "OUT"

    def is_tap_start_or_stop(self):
        return self.is_tap_start() or self.is_tap_stop()

    def is_tap_start_and_stop(self):
        return self.is_tap_start() and self.is_tap_stop()

    def is_tap_in_or_out(self):
        return self.is_tap_in() or self.is_tap_out()

    def is_tap_in_and_out(self):
        return self.is_tap_in() and self.is_tap_out()

    def __init__(self, sales_activity_model=None):
        if sales_activity_model is not None:
            self.id = sales_activity_model.id
            self.user_id = sales_activity_model.user_id
            self.visit_plan_id = sales_activity_model.visit_plan_id
            self.nfc_code = sales_activity_model.nfc_code
            self.tap_nfc_date = sales_activity_model.tap_nfc_date
            self.tap_nfc_type = sales_activity_model.tap_nfc_type
            self.route_breadcrumb = sales_activity_model.route_breadcrumb
            self.distance = sales_activity_model.distance
            self.create_date = sales_activity_model.create_date
            self.update_date = sales_activity_model.update_date


class SalesActivityBreadcrumbModel(Base):
    __tablename__ = 'sales_activity_breadcrumb'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    visit_plan_id = Column(BigInteger)
    lat = Column(FLOAT)
    lng = Column(FLOAT)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, sales_activity_breadcrumb_model=None):
        if sales_activity_breadcrumb_model is not None:
            self.id = sales_activity_breadcrumb_model.id
            self.user_id = sales_activity_breadcrumb_model.user_id
            self.visit_plan_id = sales_activity_breadcrumb_model.visit_plan_id
            self.lat = sales_activity_breadcrumb_model.lat
            self.lng = sales_activity_breadcrumb_model.lng
            self.create_date = sales_activity_breadcrumb_model.create_date
            self.update_date = sales_activity_breadcrumb_model.update_date


class LogisticActivityModel(Base):
    __tablename__ = 'logistic_activity'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    delivery_plan_id = Column(BigInteger)
    nfc_code = Column(VARCHAR)
    tap_nfc_date = Column(TIMESTAMP)
    tap_nfc_type = Column(VARCHAR)
    route_breadcrumb = Column(JSON)
    distance = Column(FLOAT)
    total_distance = Column(FLOAT)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, logistic_activity_model=None):
        if logistic_activity_model is not None:
            self.id = logistic_activity_model.id
            self.user_id = logistic_activity_model.user_id
            self.delivery_plan_id = logistic_activity_model.delivery_plan_id
            self.nfc_code = logistic_activity_model.nfc_code
            self.tap_nfc_date = logistic_activity_model.tap_nfc_date
            self.tap_nfc_type = logistic_activity_model.tap_nfc_type
            self.route_breadcrumb = logistic_activity_model.route_breadcrumb
            self.distance = logistic_activity_model.distance
            self.total_distance = logistic_activity_model.total_distance
            self.create_date = logistic_activity_model.create_date
            self.update_date = logistic_activity_model.update_date


class LogisticActivityBreadcrumbModel(Base):
    __tablename__ = 'logistic_activity_breadcrumb'

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    delivery_plan_id = Column(BigInteger)
    lat = Column(FLOAT)
    lng = Column(FLOAT)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, logistic_activity_breadcrumb_model=None):
        if logistic_activity_breadcrumb_model is not None:
            self.id = logistic_activity_breadcrumb_model.id
            self.user_id = logistic_activity_breadcrumb_model.user_id
            self.delivery_plan_id = logistic_activity_breadcrumb_model.delivery_plan_id
            self.lat = logistic_activity_breadcrumb_model.lat
            self.lng = logistic_activity_breadcrumb_model.lng
            self.create_date = logistic_activity_breadcrumb_model.create_date
            self.update_date = logistic_activity_breadcrumb_model.update_date


class BreakTimeModel(Base):
    __tablename__ = 'break_time'

    id = Column(BigInteger, primary_key=True)
    visit_plan_id = Column(BigInteger)
    delivery_plan_id = Column(BigInteger)
    user_id = Column(BigInteger)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    break_time = Column(BigInteger)

    def __init__(self, break_time_model=None):
        if break_time_model is not None:
            self.id = break_time_model.id
            self.visit_plan_id = break_time_model.visit_plan_id
            self.delivery_plan_id = break_time_model.delivery_plan_id
            self.user_id = break_time_model.user_id
            self.create_date = break_time_model.create_date
            self.update_date = break_time_model.update_date
            self.break_time = break_time_model.break_time


class IdleTimeModel(Base):
    __tablename__ = 'idle_time'

    id = Column(BigInteger, primary_key=True)
    visit_plan_id = Column(BigInteger)
    delivery_plan_id = Column(BigInteger)
    user_id = Column(BigInteger)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    idle_time = Column(BigInteger)

    def __init__(self, idle_time_model=None):
        if idle_time_model is not None:
            self.id = idle_time_model.id
            self.visit_plan_id = idle_time_model.visit_plan_id
            self.delivery_plan_id = idle_time_model.delivery_plan_id
            self.user_id = idle_time_model.user_id
            self.create_date = idle_time_model.create_date
            self.update_date = idle_time_model.update_date
            self.idle_time = idle_time_model.break_time
