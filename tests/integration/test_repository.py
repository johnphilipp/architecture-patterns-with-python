# pylint: disable=protected-access
from sqlalchemy import text
from allocation.domain import model
from allocation.adapters import repository


def test_repository_can_save_an_institution(session):
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com", "CHE123", "https://hr.ch")

    repo = repository.SqlAlchemyInstitutionRepository(session)
    repo.add(institution)
    session.commit()

    rows = session.execute(
        text('SELECT name, industry, website, uid, handelsregister_url FROM "institutions"')
    )
    assert list(rows) == [("TechCorp", "Technology", "https://techcorp.com", "CHE123", "https://hr.ch")]


def test_repository_can_retrieve_institution_with_persons_and_details(session):
    # Create institution with persons via domain
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")
    agent_output = model.AgentOutput(
        persons=[model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john")]
    )
    institution.update_persons_from_agent(agent_output)

    # Save and get ID
    repo = repository.SqlAlchemyInstitutionRepository(session)
    repo.add(institution)
    session.commit()
    institution_id = institution.id

    # Retrieve
    retrieved = repo.get(institution_id)

    assert retrieved.name == "TechCorp"
    assert len(retrieved.persons) == 1
    person = list(retrieved.persons)[0]
    assert person.first_name == "John"
    assert len(person.person_details) == 1