from sqlalchemy import Column, BigInteger, VARCHAR, TIMESTAMP, Integer, JSON, Text

from rest.configuration import Base


class InboxModel(Base):
    __tablename__ = 'inbox'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(VARCHAR)
    date = Column(TIMESTAMP)
    message = Column(Text)
    payload = Column(JSON)
    category = Column(VARCHAR)
    user_id = Column(BigInteger)
    from_id = Column(BigInteger)
    create_date = Column(TIMESTAMP)
    update_date = Column(TIMESTAMP)

    def __init__(self, inbox_model=None):
        if inbox_model is not None:
            self.id = inbox_model.id
            self.title = inbox_model.title
            self.date = inbox_model.date
            self.message = inbox_model.message
            self.payload = inbox_model.payload
            self.category = inbox_model.category
            self.user_id = inbox_model.user_id
            self.from_id = inbox_model.from_id
            self.create_date = inbox_model.create_date
            self.update_date = inbox_model.create_date
