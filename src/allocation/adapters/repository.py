import abc
from allocation.domain import model


class AbstractInstitutionRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, institution: model.Institution):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, institution_id: int) -> model.Institution:
        raise NotImplementedError


class SqlAlchemyInstitutionRepository(AbstractInstitutionRepository):
    def __init__(self, session):
        self.session = session

    def add(self, institution):
        self.session.add(institution)

    def get(self, institution_id):
        return self.session.query(model.Institution).filter_by(id=institution_id).one()

    def list(self):
        return self.session.query(model.Institution).all()
