from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text

from rest.configuration import Base


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_name = Column(VARCHAR)
    code = Column(VARCHAR)
    have_asset = Column(Integer)
    asset = Column(JSON)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    permissions = Column(JSON)
    is_approval = Column(Integer)
    approval_by = Column(BigInteger)
    is_delete_approval = Column(Integer)
    is_delete_approval_by = Column(BigInteger)
    create_by = Column(BigInteger)
    is_deleted = Column(Integer)
    is_delete_count = Column(BigInteger)

    def __init__(self, user_group_model=None):
        if user_group_model is not None:
            self.id = user_group_model.id
            self.group_name = user_group_model.group_name
            self.code = user_group_model.code
            self.have_asset = user_group_model.have_asset
            self.asset = user_group_model.asset
            self.create_date = user_group_model.create_date
            self.update_date = user_group_model.update_date
            self.permissions = user_group_model.permissions
            self.is_approval = user_group_model.is_approval
            self.is_delete_approval = user_group_model.is_delete_approval
            self.is_delete_approval_by = user_group_model.is_delete_approval_by
            self.create_by = user_group_model.create_by
            self.is_deleted = user_group_model.is_deleted
            self.is_delete_count = user_group_model.is_delete_count
