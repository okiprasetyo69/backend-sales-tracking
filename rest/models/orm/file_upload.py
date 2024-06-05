from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer

from rest.configuration import Base


class FileUploadModel(Base):
    __tablename__ = 'file_upload'

    id = Column(BigInteger, primary_key=True)
    file_name = Column(VARCHAR)
    file_name_origin = Column(VARCHAR)
    table_name = Column(VARCHAR)
    status = Column(Integer)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)
    create_by = Column(BigInteger)
    approval_by = Column(BigInteger)

    def __init__(self, file_upload_model=None):
        if file_upload_model is not None:
            self.id = file_upload_model.id
            self.file_name = file_upload_model.file_name
            self.file_name_origin = file_upload_model.file_name_origin
            self.table_name = file_upload_model.table_name
            self.status = file_upload_model.status
            self.create_date = file_upload_model.create_date
            self.update_date = file_upload_model.update_date
            self.create_by = file_upload_model.create_by
            self.approval_by = file_upload_model.approval_by
