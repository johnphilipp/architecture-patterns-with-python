import pytest
from allocation.adapters import repository, agent, handelsregister
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


class FakeHandelsregister(handelsregister.AbstractHandelsregister):
    def __init__(self, persons_to_return):
        self.persons_to_return = persons_to_return

    def fetch_persons(self, handelsregister_input):
        return model.HandelsregisterOutput(persons=self.persons_to_return)


def test_add_institution():
    uow = FakeUnitOfWork()
    services.add_institution("TechCorp", "Technology", "https://techcorp.com", uow)
    assert uow.institutions.get(1) is not None
    assert uow.committed


def test_add_institution_with_uid_and_handelsregister_url():
    uow = FakeUnitOfWork()
    services.add_institution(
        "TechCorp", "Technology", "https://techcorp.com", uow,
        "CHE123456789", "https://handelsregister.ch/CHE123456789"
    )
    institution = uow.institutions.get(1)
    assert institution.uid == "CHE123456789"
    assert institution.handelsregister_url == "https://handelsregister.ch/CHE123456789"
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
    assert uow.committed


def test_update_from_website_creates_person_details():
    uow = FakeUnitOfWork()
    services.add_institution("TechCorp", "Technology", "https://techcorp.com", uow)

    fake_agent = FakeAgent([
        model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
    ])

    services.update_from_website(1, uow, fake_agent)

    institution = uow.institutions.get(1)
    person = list(institution.persons)[0]
    assert len(person.person_details) == 1
    detail = list(person.person_details)[0]
    assert detail.source_url == "https://techcorp.com/team/john"
    assert detail.email == "john@example.com"
    assert detail.phone == "+1-555-0100"


def test_update_from_website_errors_for_invalid_institution_id():
    uow = FakeUnitOfWork()
    fake_agent = FakeAgent([])

    with pytest.raises(model.InstitutionNotFound, match="Institution with id 999 not found"):
        services.update_from_website(999, uow, fake_agent)


def test_update_from_handelsregister_adds_persons():
    uow = FakeUnitOfWork()
    services.add_institution(
        "TechCorp", "Technology", "https://techcorp.com", uow,
        "CHE123456789", "https://handelsregister.ch/CHE123456789"
    )

    fake_hr = FakeHandelsregister([
        model.HandelsregisterPerson("Max Hans Müller", "Geschäftsführer"),
        model.HandelsregisterPerson("Anna Schmidt", "Verwaltungsrätin"),
    ])

    services.update_from_handelsregister(1, uow, fake_hr)

    institution = uow.institutions.get(1)
    assert len(institution.persons) == 2
    assert uow.committed


def test_update_from_handelsregister_parses_names_correctly():
    uow = FakeUnitOfWork()
    services.add_institution(
        "TechCorp", "Technology", "https://techcorp.com", uow,
        "CHE123456789", "https://handelsregister.ch/CHE123456789"
    )

    fake_hr = FakeHandelsregister([
        model.HandelsregisterPerson("Max Hans Müller", "Geschäftsführer"),
    ])

    services.update_from_handelsregister(1, uow, fake_hr)

    institution = uow.institutions.get(1)
    person = list(institution.persons)[0]
    assert person.first_name == "Max Hans"
    assert person.last_name == "Müller"


def test_update_from_handelsregister_errors_when_url_missing():
    uow = FakeUnitOfWork()
    # Add institution WITHOUT handelsregister_url
    services.add_institution("TechCorp", "Technology", "https://techcorp.com", uow)

    fake_hr = FakeHandelsregister([])

    with pytest.raises(model.HandelsregisterUrlMissing, match="does not have a handelsregister_url"):
        services.update_from_handelsregister(1, uow, fake_hr)


def test_update_from_handelsregister_errors_for_invalid_institution_id():
    uow = FakeUnitOfWork()
    fake_hr = FakeHandelsregister([])

    with pytest.raises(model.InstitutionNotFound, match="Institution with id 999 not found"):
        services.update_from_handelsregister(999, uow, fake_hr)


def test_combining_website_and_handelsregister_data():
    """
    Test that calling both services on same institution creates persons with multiple details
    """
    uow = FakeUnitOfWork()
    services.add_institution(
        "TechCorp", "Technology", "https://techcorp.com", uow,
        "CHE123456789", "https://handelsregister.ch/CHE123456789"
    )

    # Add from website
    fake_agent = FakeAgent([
        model.AgentPerson("John", "Doe", "john@techcorp.com", "+1-555-0100", "https://techcorp.com/team/john"),
    ])
    services.update_from_website(1, uow, fake_agent)

    # Add from Handelsregister (same person)
    fake_hr = FakeHandelsregister([
        model.HandelsregisterPerson("John Doe", "Geschäftsführer"),
    ])
    services.update_from_handelsregister(1, uow, fake_hr)

    # Should have 1 person with 2 details
    institution = uow.institutions.get(1)
    assert len(institution.persons) == 1
    person = list(institution.persons)[0]
    assert len(person.person_details) == 2