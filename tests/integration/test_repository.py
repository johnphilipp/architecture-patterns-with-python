# pylint: disable=protected-access
from sqlalchemy import text
from allocation.domain import model
from allocation.adapters import repository


def test_repository_can_save_an_institution(session):
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    repo = repository.SqlAlchemyInstitutionRepository(session)
    repo.add(institution)
    session.commit()

    rows = session.execute(
        text('SELECT name, industry, website FROM "institutions"')
    )
    assert list(rows) == [("TechCorp", "Technology", "https://techcorp.com")]


def insert_institution(session, name, industry, website):
    session.execute(
        text("INSERT INTO institutions (name, industry, website)"
        " VALUES (:name, :industry, :website)"),
        dict(name=name, industry=industry, website=website),
    )
    [[institution_id]] = session.execute(
        text("SELECT id FROM institutions WHERE name=:name"),
        dict(name=name),
    )
    return institution_id


def insert_person(session, institution_id, first_name, last_name, source_url, email, phone):
    session.execute(
        text("INSERT INTO persons (institution_id, first_name, last_name, source_url, email, phone, job_title)"
        " VALUES (:institution_id, :first_name, :last_name, :source_url, :email, :phone, '')"),
        dict(
            institution_id=institution_id,
            first_name=first_name,
            last_name=last_name,
            source_url=source_url,
            email=email,
            phone=phone,
        ),
    )


def test_repository_can_retrieve_an_institution_with_persons(session):
    institution_id = insert_institution(session, "TechCorp", "Technology", "https://techcorp.com")
    insert_person(session, institution_id, "John", "Doe", "https://techcorp.com/team/john", "john@example.com", "+1-555-0100")
    insert_person(session, institution_id, "Jane", "Smith", "https://techcorp.com/team/jane", "jane@example.com", "+1-555-0101")

    repo = repository.SqlAlchemyInstitutionRepository(session)
    retrieved = repo.get(institution_id)

    assert retrieved.name == "TechCorp"
    assert retrieved.industry == "Technology"
    assert retrieved.website == "https://techcorp.com"
    assert len(retrieved.persons) == 2

    persons_list = list(retrieved.persons)
    assert any(p.first_name == "John" and p.last_name == "Doe" for p in persons_list)
    assert any(p.first_name == "Jane" and p.last_name == "Smith" for p in persons_list)