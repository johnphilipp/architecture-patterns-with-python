"""
Unit tests for Institution and Person domain models with PersonDetail
"""
from allocation.domain import model


def test_person_equality_based_on_first_and_last_name_only():
    person1 = model.Person("John", "Doe")
    person2 = model.Person("John", "Doe")
    person3 = model.Person("Jane", "Doe")

    # Same first_name and last_name = equal
    assert person1 == person2

    # Different first_name = not equal
    assert person1 != person3

    # Can be used in sets
    person_set = {person1, person2, person3}
    assert len(person_set) == 2  # person1 and person2 are duplicates


def test_adding_detail_to_person():
    person = model.Person("John", "Doe")
    detail = model.PersonDetail("CEO", "https://example.com/john", "john@example.com", "+1-555-0100")

    person.add_or_update_detail(detail)

    assert len(person.person_details) == 1
    assert detail in person.person_details


def test_updating_existing_detail_by_source_url():
    person = model.Person("John", "Doe")

    # Add initial detail
    detail1 = model.PersonDetail("CEO", "https://example.com/john", "old@example.com", "+1-555-0100")
    person.add_or_update_detail(detail1)

    # Agent found new detail from same source_url
    detail2 = model.PersonDetail("CTO", "https://example.com/john", "new@example.com", "+1-555-9999")
    person.add_or_update_detail(detail2)

    # Should still have only 1 detail
    assert len(person.person_details) == 1

    # Fields should have NOT been updated
    updated_detail = list(person.person_details)[0]
    assert updated_detail.job_title == "CEO"
    assert updated_detail.email == "old@example.com"
    assert updated_detail.phone == "+1-555-0100"


def test_adding_multiple_details_from_different_sources():
    person = model.Person("John", "Doe")

    website_detail = model.PersonDetail("CEO", "https://company.com/team/john", "john@company.com", "+1-555-0100")
    hr_detail = model.PersonDetail("Geschäftsführer", "https://handelsregister.ch/person/john-doe", "", "")

    person.add_or_update_detail(website_detail)
    person.add_or_update_detail(hr_detail)

    assert len(person.person_details) == 2


def test_institution_update_persons_from_agent_creates_person_and_detail():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")
    agent_output = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
        ]
    )

    institution.update_persons_from_agent(agent_output)

    assert len(institution.persons) == 1
    person = list(institution.persons)[0]
    assert person.first_name == "John"
    assert person.last_name == "Doe"
    assert len(person.person_details) == 1


def test_institution_update_persons_from_agent_updates_existing_person_detail():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # First update
    agent_output_1 = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john.old@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
        ]
    )
    institution.update_persons_from_agent(agent_output_1)

    # Second update with same person and source_url
    agent_output_2 = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john.new@example.com", "+1-555-9999", "https://techcorp.com/team/john"),
        ]
    )
    institution.update_persons_from_agent(agent_output_2)

    # Should still have 1 person with 1 detail
    assert len(institution.persons) == 1
    person = list(institution.persons)[0]
    assert len(person.person_details) == 1

    # Detail should have NOT been updated
    detail = list(person.person_details)[0]
    assert detail.email == "john.old@example.com"
    assert detail.phone == "+1-555-0100"


def test_institution_update_persons_from_agent_adds_new_persons():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # First update - John
    agent_output_1 = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
        ]
    )
    institution.update_persons_from_agent(agent_output_1)

    # Second update - Jane
    agent_output_2 = model.AgentOutput(
        persons=[
            model.AgentPerson("Jane", "Smith", "jane@example.com", "+1-555-0101", "https://techcorp.com/team/jane"),
        ]
    )
    institution.update_persons_from_agent(agent_output_2)

    # Should have 2 persons
    assert len(institution.persons) == 2


def test_institution_parse_full_name():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # Multi-word name
    first, last = institution._parse_full_name("John Michael Doe")
    assert first == "John Michael"
    assert last == "Doe"

    # Two-word name
    first, last = institution._parse_full_name("John Doe")
    assert first == "John"
    assert last == "Doe"

    # Single word
    first, last = institution._parse_full_name("Madonna")
    assert first == "Madonna"
    assert last == ""

    # Empty string
    first, last = institution._parse_full_name("")
    assert first == ""
    assert last == ""


def test_institution_update_persons_from_handelsregister():
    institution = model.Institution(
        "TechCorp", "Technology", "https://techcorp.com",
        "CHE123456789", "https://handelsregister.ch/CHE123456789"
    )

    hr_output = model.HandelsregisterOutput(
        persons=[
            model.HandelsregisterPerson("Max Hans Müller", "Geschäftsführer"),
            model.HandelsregisterPerson("Anna Schmidt", "Verwaltungsrätin"),
        ]
    )

    institution.update_persons_from_handelsregister(hr_output)

    # Should create 2 persons
    assert len(institution.persons) == 2

    # Check first person
    persons_list = list(institution.persons)
    max_person = next(p for p in persons_list if p.last_name == "Müller")
    assert max_person.first_name == "Max Hans"
    assert len(max_person.person_details) == 1
    detail = list(max_person.person_details)[0]
    assert detail.job_title == "Geschäftsführer"
    assert "handelsregister" in detail.source_url


def test_institution_combining_agent_and_handelsregister_data():
    """
    Test that the same person can have details from both sources
    """
    institution = model.Institution(
        "TechCorp", "Technology", "https://techcorp.com",
        "CHE123456789", "https://handelsregister.ch/CHE123456789"
    )

    # Add from website
    agent_output = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john@techcorp.com", "+1-555-0100", "https://techcorp.com/team/john"),
        ]
    )
    institution.update_persons_from_agent(agent_output)

    # Add from Handelsregister (same person!)
    hr_output = model.HandelsregisterOutput(
        persons=[
            model.HandelsregisterPerson("John Doe", "Geschäftsführer"),
        ]
    )
    institution.update_persons_from_handelsregister(hr_output)

    # Should have 1 person with 2 details
    assert len(institution.persons) == 1
    person = list(institution.persons)[0]
    assert len(person.person_details) == 2

    # Check both details exist
    details_list = list(person.person_details)
    assert any("techcorp.com" in d.source_url for d in details_list)
    assert any("handelsregister" in d.source_url for d in details_list)


def test_person_detail_equality_based_on_source_url():
    detail1 = model.PersonDetail("CEO", "https://example.com/john", "john@example.com")
    detail2 = model.PersonDetail("CTO", "https://example.com/john", "different@example.com")
    detail3 = model.PersonDetail("CEO", "https://other.com/john", "john@example.com")

    # Same source_url = equal
    assert detail1 == detail2

    # Different source_url = not equal
    assert detail1 != detail3

    # Can be used in sets
    detail_set = {detail1, detail2, detail3}
    assert len(detail_set) == 2  # detail1 and detail2 are duplicates