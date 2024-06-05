from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text

from rest.configuration import Base


class DeliveryCycleModel(Base):
    __tablename__ = 'delivery_cycle'

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

    def __init__(self, delivery_cycle_model=None):
        if delivery_cycle_model is not None:
            self.id = delivery_cycle_model.id
            self.user_id = delivery_cycle_model.user_id
            self.asset_id = delivery_cycle_model.asset_id
            self.cycle_number = delivery_cycle_model.cycle_number
            self.cycle_monday = delivery_cycle_model.cycle_monday
            self.cycle_tuesday = delivery_cycle_model.cycle_tuesday
            self.cycle_wednesday = delivery_cycle_model.cycle_wednesday
            self.cycle_thursday = delivery_cycle_model.cycle_thursday
            self.cycle_friday = delivery_cycle_model.cycle_friday
            self.cycle_saturday = delivery_cycle_model.cycle_saturday
            self.cycle_sunday = delivery_cycle_model.cycle_sunday
            self.create_date = delivery_cycle_model.create_date
            self.update_date = delivery_cycle_model.update_date
            self.is_approval = delivery_cycle_model.is_approval
            self.is_delete_approval = delivery_cycle_model.is_delete_approval
            self.is_delete_approval_by = delivery_cycle_model.is_delete_approval_by
            self.create_by = delivery_cycle_model.create_by
            self.edit_data = delivery_cycle_model.edit_data
            self.is_deleted = delivery_cycle_model.is_deleted
            self.is_delete_count = delivery_cycle_model.is_delete_count


class DeliveryPlanModel(Base):
    __tablename__ = 'delivery_plan'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    date = Column(TIMESTAMP)
    asset_id = Column(BigInteger)
    route = Column(JSON)
    destination = Column(JSON)
    destination_new = Column(JSON)
    start_route_branch_id = Column(BigInteger)
    end_route_branch_id = Column(BigInteger)
    packing_slip_id = Column(JSON)
    is_use_route = Column(Integer)
    status = Column(Integer)
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

    def __init__(self, delivery_plan_model=None):
        if delivery_plan_model is not None:
            self.id = delivery_plan_model.id
            self.user_id = delivery_plan_model.user_id
            self.date = delivery_plan_model.date
            self.asset_id = delivery_plan_model.asset_id
            self.route = delivery_plan_model.route
            self.destination = delivery_plan_model.destination
            self.destination_new = delivery_plan_model.destination_new
            self.start_route_branch_id = delivery_plan_model.start_route_branch_id
            self.end_route_branch_id = delivery_plan_model.end_route_branch_id
            self.packing_slip_id = delivery_plan_model.packing_slip_id
            self.is_user_route = delivery_plan_model.is_user_route
            self.status = delivery_plan_model.status
            self.create_date = delivery_plan_model.create_date
            self.update_date = delivery_plan_model.update_date
            self.is_approval = delivery_plan_model.is_approval
            self.approval_by = delivery_plan_model.approval_by
            self.is_delete_approval = delivery_plan_model.is_delete_approval
            self.is_delete_approval_by = delivery_plan_model.is_delete_approval_by
            self.create_by = delivery_plan_model.create_by
            self.edit_data = delivery_plan_model.edit_data
            self.is_deleted = delivery_plan_model.is_deleted
            self.is_delete_count = delivery_plan_model.is_delete_count


class DeliveryModel(Base):
    __tablename__ = 'delivery'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    packing_slip_code = Column(VARCHAR)
    customer_code = Column(VARCHAR)
    delivery_date = Column(TIMESTAMP)
    user_id = Column(BigInteger)
    deliery_plan_id = Column(BigInteger)
    product = Column(JSON)
    is_accepted = Column(Integer)
    accepted_by = Column(VARCHAR)
    is_rejected = Column(Integer)
    rejected_by = Column(VARCHAR)
    reason_reject = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, delivery_model=None):
        if delivery_model is not None:
            self.id = delivery_model.id
            self.packing_slip_code = delivery_model.packing_slip_code
            self.customer_code = delivery_model.customer_code
            self.delivery_date = delivery_model.delivery_date
            self.user_id = delivery_model.user_id
            self.product = delivery_model.product
            self.is_accepted = delivery_model.is_accepted
            self.accepted_by = delivery_model.accepted_by
            self.is_rejected = delivery_model.is_rejected
            self.rejected_by = delivery_model.rejected_by
            self.reason_reject = delivery_model.reason_reject
            self.create_date = delivery_model.create_date
            self.update_date = delivery_model.update_date


class DeliveryPlanSummaryModel(Base):
    __tablename__ = 'delivery_plan_summary'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    plan_id = Column(BigInteger)
    customer_code = Column(VARCHAR)
    notes = Column(Text)
    visit_images = Column(JSON)
    have_competitor = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    create_by = Column(BigInteger)

    def __init__(self, delivery_plan_summary_model=None):
        if delivery_plan_summary_model is not None:
            self.id = delivery_plan_summary_model.id
            self.plan_id = delivery_plan_summary_model.plan_id
            self.customer_code = delivery_plan_summary_model.customer_code
            self.notes = delivery_plan_summary_model.notes
            self.visit_images = delivery_plan_summary_model.visit_images
            self.have_competitor = delivery_plan_summary_model.have_competitor
            self.create_date = delivery_plan_summary_model.create_date
            self.update_date = delivery_plan_summary_model.update_date
            self.create_by = delivery_plan_summary_model.create_by
