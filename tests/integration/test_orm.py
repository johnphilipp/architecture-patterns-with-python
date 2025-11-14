from allocation.domain import model
from sqlalchemy import text


def test_person_detail_mapper_can_save(session):
    detail = model.PersonDetail("CEO", "https://example.com/john", "john@example.com", "+1-555-0100")
    session.add(detail)
    session.commit()

    rows = list(session.execute(
        text('SELECT job_title, source_url, email, phone FROM "person_details"')
    ))
    assert rows == [("CEO", "https://example.com/john", "john@example.com", "+1-555-0100")]


def test_person_mapper_can_save(session):
    person = model.Person("John", "Doe")
    session.add(person)
    session.commit()

    rows = list(session.execute(
        text('SELECT first_name, last_name FROM "persons"')
    ))
    assert rows == [("John", "Doe")]


def test_person_with_details_can_save(session):
    person = model.Person("John", "Doe")
    detail = model.PersonDetail("CEO", "https://example.com/john", "john@example.com", "+1-555-0100")
    person.add_or_update_detail(detail)

    session.add(person)
    session.commit()

    # Check person
    person_rows = list(session.execute(text('SELECT first_name, last_name FROM "persons"')))
    assert len(person_rows) == 1

    # Check details
    detail_rows = list(session.execute(text('SELECT job_title, source_url FROM "person_details"')))
    assert len(detail_rows) == 1
    assert detail_rows[0] == ("CEO", "https://example.com/john")


def test_institution_mapper_can_save(session):
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com", "CHE123", "https://hr.ch")
    session.add(institution)
    session.commit()

    rows = list(session.execute(
        text('SELECT name, industry, website, uid, handelsregister_url FROM "institutions"')
    ))
    assert rows == [("TechCorp", "Technology", "https://techcorp.com", "CHE123", "https://hr.ch")]


def test_institution_with_persons_and_details(session):
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # Create persons with details via domain method
    agent_output = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
            model.AgentPerson("Jane", "Smith", "jane@example.com", "+1-555-0101", "https://techcorp.com/team/jane"),
        ]
    )
    institution.update_persons_from_agent(agent_output)

    session.add(institution)
    session.commit()

    # Check persons
    person_rows = list(session.execute(text('SELECT first_name, last_name FROM "persons"')))
    assert len(person_rows) == 2

    # Check details
    detail_rows = list(session.execute(text('SELECT source_url FROM "person_details"')))
    assert len(detail_rows) == 2


def test_retrieving_institution_with_persons_and_details(session):
    # Insert institution
    session.execute(
        text("INSERT INTO institutions (name, industry, website, uid, handelsregister_url) VALUES "
        '("TechCorp", "Technology", "https://techcorp.com", "CHE123", "https://hr.ch")')
    )
    [[institution_id]] = session.execute(text("SELECT id FROM institutions WHERE name='TechCorp'"))

    # Insert person
    session.execute(
        text(f"INSERT INTO persons (institution_id, first_name, last_name) VALUES "
        f'({institution_id}, "John", "Doe")')
    )
    [[person_id]] = session.execute(text('SELECT id FROM persons WHERE first_name="John"'))

    # Insert details
    session.execute(
        text(f"INSERT INTO person_details (person_id, job_title, email, phone, source_url) VALUES "
        f'({person_id}, "CEO", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john")')
    )

    # Retrieve institution
    institution = session.query(model.Institution).one()

    assert len(institution.persons) == 1
    person = list(institution.persons)[0]
    assert person.first_name == "John"
    assert len(person.person_details) == 1
    detail = list(person.person_details)[0]
    assert detail.job_title == "CEO"
    assert detail.email == "john@example.com"