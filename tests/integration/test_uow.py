import pytest
from sqlalchemy import text
from allocation.domain import model
from allocation.service_layer import unit_of_work


def insert_institution(session, name, industry, website):
    session.execute(
        text("INSERT INTO institutions (name, industry, website)"
        " VALUES (:name, :industry, :website)"),
        dict(name=name, industry=industry, website=website),
    )


def get_institution_persons_count(session, institution_id):
    [[count]] = session.execute(
        text("SELECT COUNT(*) FROM persons WHERE institution_id=:institution_id"),
        dict(institution_id=institution_id),
    )
    return count


def test_uow_can_retrieve_an_institution_and_update_persons(session_factory):
    session = session_factory()
    insert_institution(session, "TechCorp", "Technology", "https://techcorp.com")
    [[institution_id]] = session.execute(text("SELECT id FROM institutions WHERE name='TechCorp'"))
    session.commit()

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        institution = uow.institutions.get(institution_id)
        agent_output = model.AgentOutput(
            persons=[
                model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
            ]
        )
        institution.update_persons_from_agent(agent_output)
        uow.commit()

    count = get_institution_persons_count(session, institution_id)
    assert count == 1


def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_institution(uow.session, "TechCorp", "Technology", "https://techcorp.com")

    new_session = session_factory()
    rows = list(new_session.execute(text('SELECT * FROM "institutions"')))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_institution(uow.session, "TechCorp", "Technology", "https://techcorp.com")
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute(text('SELECT * FROM "institutions"')))
    assert rows == []