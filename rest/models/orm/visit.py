from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text, ForeignKey, or_, func, and_
from sqlalchemy.orm import relationship

from rest.configuration import Base, session
# from rest.models.orm import SalesActivityModel, BranchesModel, UserModel, EmployeeModel, DivisionModel
from rest.models.orm.activity import SalesActivityModel
from rest.models.orm.branches import BranchesModel
from rest.models.orm.customer import CustomerModel
from rest.models.orm.divisions import DivisionModel
from rest.models.orm.employee import EmployeeModel
from rest.models.orm.user import UserModel


class VisitCycleModel(Base):
    __tablename__ = 'visit_cycle'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    asset_id = Column(BigInteger)
    cycle_number = Column(Integer)
    cycle_monday = Column(JSON)
    cycle_tuesday = Column(JSON)
    cycle_wednesday = Column(JSON)
    cycle_thursday = Column(JSON)
    cycle_friday = Column(JSON)
    cycle_saturday = Column(JSON)
    cycle_sunday = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)
    is_delete_count = Column(BigInteger)

    def __init__(self, visit_cycle_model=None):
        if visit_cycle_model is not None:
            self.id = visit_cycle_model.id
            self.user_id = visit_cycle_model.user_id
            self.asset_id = visit_cycle_model.asset_id
            self.cycle_number = visit_cycle_model.cycle_number
            self.cycle_monday = visit_cycle_model.cycle_monday
            self.cycle_tuesday = visit_cycle_model.cycle_tuesday
            self.cycle_wednesday = visit_cycle_model.cycle_wednesday
            self.cycle_thursday = visit_cycle_model.cycle_thursday
            self.cycle_friday = visit_cycle_model.cycle_friday
            self.cycle_saturday = visit_cycle_model.cycle_saturday
            self.cycle_sunday = visit_cycle_model.cycle_sunday
            self.create_date = visit_cycle_model.create_date
            self.update_date = visit_cycle_model.update_date
            self.is_approval = visit_cycle_model.is_approval
            self.approval_by = visit_cycle_model.approval_by
            self.is_delete_approval = visit_cycle_model.is_delete_approval
            self.is_delete_approval_by = visit_cycle_model.is_delete_approval_by
            self.create_by = visit_cycle_model.create_by
            self.edit_data = visit_cycle_model.edit_data
            self.is_deleted = visit_cycle_model.is_deleted
            self.is_delete_count = visit_cycle_model.is_delete_count


class VisitPlanModel(Base):
    __tablename__ = 'visit_plan'

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    date = Column(TIMESTAMP)
    asset_id = Column(BigInteger)
    route = Column(JSON)
    destination = Column(JSON)
    destination_order = Column(JSON)
    destination_new = Column(JSON)
    start_route_branch_id = Column(BigInteger, ForeignKey("branches.id"))
    end_route_branch_id = Column(BigInteger, ForeignKey("branches.id"))
    invoice_id = Column(JSON)
    is_use_route = Column(Integer)
    status = Column(Integer)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    is_approval = Column(Integer)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(Integer)
    approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    edit_data = Column(JSON)
    is_deleted = Column(Integer)
    is_delete_count = Column(BigInteger)

    users = relationship("UserModel")
    branch_start = relationship("BranchesModel", foreign_keys=[start_route_branch_id])
    branch_end = relationship("BranchesModel", foreign_keys=[end_route_branch_id])

    def __init__(self, visit_plan_model=None):
        if visit_plan_model is not None:
            self.id = visit_plan_model.id
            self.user_id = visit_plan_model.user_id
            self.date = visit_plan_model.date
            self.asset_id = visit_plan_model.asset_id
            self.route = visit_plan_model.route
            self.destination = visit_plan_model.destination
            self.destination_order = visit_plan_model.destination_order
            self.destination_new = visit_plan_model.destination_new
            self.start_route_branch_id = visit_plan_model.start_route_branch_id
            self.end_route_branch_id = visit_plan_model.end_route_branch_id
            self.invoice_id = visit_plan_model.invoice_id
            self.is_use_route = visit_plan_model.is_use_route
            self.status = visit_plan_model.status
            self.create_date = visit_plan_model.create_date
            self.update_date = visit_plan_model.update_date
            self.is_approval = visit_plan_model.is_approval
            self.is_delete_approval = visit_plan_model.is_delete_approval
            self.is_delete_approval_by = visit_plan_model.is_delete_approval_by
            self.approval_by = visit_plan_model.approval_by
            self.create_by = visit_plan_model.create_by
            self.edit_data = visit_plan_model.edit_data
            self.is_deleted = visit_plan_model.is_deleted
            self.is_delete_count = visit_plan_model.is_delete_count
            self.users = visit_plan_model.users
            self.branch_start = visit_plan_model.branch_start
            self.branch_end = visit_plan_model.branch_end

    def activity_query(self):
        return session.query(SalesActivityModel).filter(
            and_(
                or_(
                    SalesActivityModel.id.in_(
                        session.query(func.min(SalesActivityModel.id)).filter(
                            SalesActivityModel.tap_nfc_type == "START"
                        ).group_by(
                            SalesActivityModel.user_id, SalesActivityModel.visit_plan_id, SalesActivityModel.nfc_code
                        ).subquery()
                    ),
                    SalesActivityModel.id.in_(
                        session.query(func.max(SalesActivityModel.id)).filter(
                            SalesActivityModel.tap_nfc_type == "STOP"
                        ).group_by(
                            SalesActivityModel.user_id, SalesActivityModel.visit_plan_id, SalesActivityModel.nfc_code
                        ).subquery()
                    ),
                    SalesActivityModel.id.in_(
                        session.query(SalesActivityModel.id).filter(
                            SalesActivityModel.tap_nfc_type == "IN"
                        ).subquery()
                    ),
                    SalesActivityModel.id.in_(
                        session.query(SalesActivityModel.id).filter(
                            SalesActivityModel.tap_nfc_type == "OUT"
                        ).subquery()
                    ),
                ),
                SalesActivityModel.visit_plan_id == self.id,
            )
        ).all()

    def plan_activity(self):
        list_plan_activity = []
        list_visited_customer = []
        for x in self.activity_query():
            activity = SalesActivityModel(x)
            new_activity = {
                'tap_nfc_date': activity.tap_nfc_date,
                'create_date': activity.create_date,
                'update_date': activity.update_date,
                'branch_name': None,
                'branch_location': None,
                'customer_code': None,
                'customer_name': None,
                'customer_address': None,
                'route_breadcrumb': None
            }
            if activity.is_tap_start_or_stop():
                branch = BranchesModel(
                    session.query(BranchesModel).filter(BranchesModel.id == activity.nfc_code).one()
                )
                new_activity['branch_name'] = branch.name
                new_activity['branch_location'] = branch.address

            if activity.is_tap_in_or_out():
                customer = CustomerModel(
                    session.query(CustomerModel).filter(CustomerModel.code == activity.nfc_code).one()
                )
                new_activity['customer_code'] = customer.nfcid
                new_activity['customer_name'] = customer.name
                new_activity['customer_address'] = customer.address

            if activity.route_breadcrumb is not None:
                new_activity['route_breadcrumb'] = activity.route_breadcrumb

            if activity.user is not None:
                user = UserModel(activity.user)
                employee_user = EmployeeModel(user.employee)
                branch_user = BranchesModel(user.branch)
                division_user = DivisionModel(user.division)
                new_activity['user']['username'] = user.username
                new_activity['user']['employee_id'] = user.employee_id
                new_activity['user']['name'] = employee_user.name
                new_activity['user']['branch_id'] = user.branch_id
                new_activity['user']['branch_name'] = branch_user.name
                new_activity['user']['division_id'] = user.division_id
                new_activity['user']['division_name'] = division_user.division_name
            else:
                new_activity['user'] = {}

            if activity.nfc_code is not None and new_activity['customer_code'] is not None:
                if len(list_visited_customer) > 0:
                    if activity.nfc_code not in list_visited_customer:
                        list_visited_customer.append(activity.nfc_code)
                else:
                    list_visited_customer.append(activity.nfc_code)

            list_plan_activity.append(new_activity)

        return list_plan_activity

    def visited_customer(self):
        plan_activity = self.plan_activity()
        if len(plan_activity) is not 0:
            for plan in plan_activity:
                activity = SalesActivityModel(plan)


class VisitPlanSummaryModel(Base):
    __tablename__ = 'visit_plan_summary'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_id = Column(BigInteger)
    customer_code = Column(VARCHAR)
    notes = Column(Text)
    visit_images = Column(JSON)
    have_competitor = Column(Integer)
    competitor_images = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    create_by = Column(BigInteger)

    def __init__(self, visit_plan_summary_model=None):
        if visit_plan_summary_model is not None:
            self.id = visit_plan_summary_model.id
            self.plan_id = visit_plan_summary_model.plan_id
            self.customer_code = visit_plan_summary_model.customer_code
            self.notes = visit_plan_summary_model.notes
            self.visit_images = visit_plan_summary_model.visit_images
            self.have_competitor = visit_plan_summary_model.have_competitor
            self.competitor_images = visit_plan_summary_model.competitor_images
            self.create_date = visit_plan_summary_model.create_date
            self.update_date = visit_plan_summary_model.update_date
            self.create_by = visit_plan_summary_model.create_by
