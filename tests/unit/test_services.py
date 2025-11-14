import pytest
from allocation.adapters import repository, agent
from allocation.domain import model
from allocation.service_layer import services, unit_of_work


class FakeInstitutionRepository(repository.AbstractInstitutionRepository):
    def __init__(self, institutions):
        self._institutions = set(institutions)
        self._next_id = 1

    def add(self, institution):
        # Simulate auto-incrementing ID
        institution.id = self._next_id
        self._next_id += 1
        self._institutions.add(institution)

    def get(self, institution_id):
        try:
            return next(i for i in self._institutions if i.id == institution_id)
        except StopIteration:
            from sqlalchemy.exc import NoResultFound
            raise NoResultFound()

    def list(self):
        return list(self._institutions)


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.institutions = FakeInstitutionRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeAgent(agent.AbstractAgent):
    def __init__(self, persons_to_return):
        self.persons_to_return = persons_to_return

    def fetch_persons(self, agent_input):
        return model.AgentOutput(persons=self.persons_to_return)


def test_add_institution():
    uow = FakeUnitOfWork()
    services.add_institution("TechCorp", "Technology", "https://techcorp.com", uow)
    assert uow.institutions.get(1) is not None
    assert uow.committed


def test_add_institution_commits():
    uow = FakeUnitOfWork()
    services.add_institution("TechCorp", "Technology", "https://techcorp.com", uow)
    assert uow.committed


def test_update_from_website_returns_correctly():
    uow = FakeUnitOfWork()
    services.add_institution("TechCorp", "Technology", "https://techcorp.com", uow)

    fake_agent = FakeAgent([
        model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
    ])

    services.update_from_website(1, uow, fake_agent)
    assert uow.committed


def test_update_from_website_adds_persons():
    uow = FakeUnitOfWork()
    services.add_institution("TechCorp", "Technology", "https://techcorp.com", uow)

    fake_agent = FakeAgent([
        model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
        model.AgentPerson("Jane", "Smith", "jane@example.com", "+1-555-0101", "https://techcorp.com/team/jane"),
    ])

    services.update_from_website(1, uow, fake_agent)

    institution = uow.institutions.get(1)
    assert len(institution.persons) == 2


def test_update_from_website_errors_for_invalid_institution_id():
    uow = FakeUnitOfWork()

    fake_agent = FakeAgent([])

    with pytest.raises(model.InstitutionNotFound, match="Institution with id 999 not found"):
        services.update_from_website(999, uow, fake_agent)