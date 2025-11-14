from allocation.domain import model
from sqlalchemy import text


def test_person_mapper_can_save_persons(session):
    person = model.Person("John", "Doe", "https://example.com/john", "john@example.com", "+1-555-0100", "CEO")
    session.add(person)
    session.commit()

    rows = list(session.execute(
        text('SELECT first_name, last_name, source_url, email, phone, job_title FROM "persons"')
    ))
    assert rows == [("John", "Doe", "https://example.com/john", "john@example.com", "+1-555-0100", "CEO")]


def test_person_mapper_can_load_persons(session):
    session.execute(
        text("INSERT INTO persons (institution_id, first_name, last_name, source_url, email, phone, job_title) VALUES "
        '(null, "John", "Doe", "https://example.com/john", "john@example.com", "+1-555-0100", "CEO"),'
        '(null, "Jane", "Smith", "https://example.com/jane", "jane@example.com", "+1-555-0101", "CTO")')
    )
    expected = [
        model.Person("John", "Doe", "https://example.com/john", "john@example.com", "+1-555-0100", "CEO"),
        model.Person("Jane", "Smith", "https://example.com/jane", "jane@example.com", "+1-555-0101", "CTO"),
    ]
    result = session.query(model.Person).all()
    assert len(result) == 2
    assert result[0].first_name == "John"
    assert result[1].first_name == "Jane"


def test_institution_mapper_can_save_institutions(session):
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")
    session.add(institution)
    session.commit()

    rows = list(session.execute(
        text('SELECT name, industry, website FROM "institutions"')
    ))
    assert rows == [("TechCorp", "Technology", "https://techcorp.com")]


def test_institution_mapper_can_load_institutions(session):
    session.execute(
        text("INSERT INTO institutions (name, industry, website) VALUES "
        '("TechCorp", "Technology", "https://techcorp.com"),'
        '("BizCorp", "Business", "https://bizcorp.com")')
    )
    institutions = session.query(model.Institution).all()
    assert len(institutions) == 2
    assert institutions[0].name == "TechCorp"
    assert institutions[1].name == "BizCorp"


def test_saving_institution_with_persons(session):
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # Use the domain method to add persons
    agent_output = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
            model.AgentPerson("Jane", "Smith", "jane@example.com", "+1-555-0101", "https://techcorp.com/team/jane"),
        ]
    )
    institution.update_persons_from_agent(agent_output)

    session.add(institution)
    session.commit()

    rows = list(session.execute(text('SELECT institution_id, first_name, last_name FROM "persons"')))
    assert len(rows) == 2
    assert rows[0][1] in ("John", "Jane")  # first_name
    assert rows[1][1] in ("John", "Jane")


def test_retrieving_institution_with_persons(session):
    session.execute(
        text("INSERT INTO institutions (name, industry, website) VALUES "
        '("TechCorp", "Technology", "https://techcorp.com")')
    )
    [[institution_id]] = session.execute(
        text("SELECT id FROM institutions WHERE name='TechCorp'")
    )
    session.execute(
        text("INSERT INTO persons (institution_id, first_name, last_name, source_url, email, phone, job_title) VALUES "
        f'({institution_id}, "John", "Doe", "https://techcorp.com/team/john", "john@example.com", "+1-555-0100", "CEO"),'
        f'({institution_id}, "Jane", "Smith", "https://techcorp.com/team/jane", "jane@example.com", "+1-555-0101", "CTO")')
    )

    institution = session.query(model.Institution).one()

    assert len(institution.persons) == 2
    persons_list = list(institution.persons)
    assert any(p.first_name == "John" for p in persons_list)
    assert any(p.first_name == "Jane" for p in persons_list)