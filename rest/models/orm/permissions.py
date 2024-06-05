from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text

from rest.configuration import Base


class PermissionsModel(Base):
    __tablename__ = 'mobile_permission_alert'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    subject = Column(VARCHAR)
    date = Column(TIMESTAMP)
    type = Column(VARCHAR)
    visit_plan_id = Column(BigInteger)
    delivery_plan_id = Column(BigInteger)
    description = Column(JSON)
    customer_code = Column(VARCHAR)
    notes = Column(Text)
    is_approved = Column(Integer)
    create_by = Column(BigInteger)
    approval_by = Column(BigInteger)
    is_rejected = Column(Integer)
    reject_by = Column(BigInteger)

    def __init__(self, permissions_model=None):
        if permissions_model is not None:
            self.id = permissions_model.id
            self.subject = permissions_model.subject
            self.date = permissions_model.date
            self.type = permissions_model.type
            self.visit_plan_id = permissions_model.visit_plan_id
            self.delivery_plan_id = permissions_model.delivery_plan_id
            self.description = permissions_model.description
            self.customer_code = permissions_model.customer_code
            self.notes = permissions_model.notes
            self.is_approved = permissions_model.is_approved
            self.create_by = permissions_model.create_by
            self.approval_by = permissions_model.approval_by
            self.is_rejected = permissions_model.is_rejected
            self.reject_by = permissions_model.reject_by
