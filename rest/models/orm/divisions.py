from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text

from rest.configuration import Base


class DivisionModel(Base):
    __tablename__ = 'divisions'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    division_code = Column(VARCHAR)
    division_name = Column(VARCHAR)
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

    def __init__(self, division_model=None):
        if division_model is not None:
            self.id = division_model.id
            self.division_code = division_model.division_code
            self.division_name = division_model.division_name
            self.create_date = division_model.create_date
            self.update_date = division_model.update_date
            self.is_approval = division_model.is_approval
            self.approval_by = division_model.approval_by
            self.is_delete_approval = division_model.is_delete_approval
            self.is_delete_approval_by = division_model.is_delete_approval_by
            self.create_by = division_model.create_by
            self.edit_data = division_model.edit_data
            self.is_deleted = division_model.is_deleted
            self.is_delete_count = division_model.is_delete_count
