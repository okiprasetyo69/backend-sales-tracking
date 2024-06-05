from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, JSON, Integer

from rest.configuration import Base


class ApprovalModel(Base):
    __tablename__ = 'data_approval'

    id = Column(BigInteger, primary_key=True)
    prefix = Column(VARCHAR)
    data_id = Column(VARCHAR)
    type = Column(VARCHAR)
    data = Column(JSON)
    create_by = Column(BigInteger)
    is_approved = Column(Integer)
    approved_by = Column(BigInteger)
    is_rejected = Column(Integer)
    rejected_by = Column(BigInteger)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    approved_date = Column(TIMESTAMP)
    rejected_date = Column(TIMESTAMP)

    def __init__(self, approval_model=None):
        if approval_model is not None:
            self.id = approval_model.id
            self.prefix = approval_model.prefix
            self.data_id = approval_model.data_id
            self.type = approval_model.type
            self.data = approval_model.data
            self.create_by = approval_model.create_by
            self.is_approved = approval_model.is_approved
            self.approved_by = approval_model.approved_by
            self.is_rejected = approval_model.is_rejected
            self.rejected_by = approval_model.rejected_by
            self.create_date = approval_model.create_date
            self.update_date = approval_model.update_date
            self.approved_date = approval_model.approved_date
            self.rejected_date = approval_model.rejected_date
