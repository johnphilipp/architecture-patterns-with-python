"""
Unit tests for Institution domain model
"""
from allocation.domain import model


def test_adding_persons_to_empty_institution():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")
    agent_output = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
            model.AgentPerson("Jane", "Smith", "jane@example.com", "+1-555-0101", "https://techcorp.com/team/jane"),
        ]
    )

    institution.update_persons_from_agent(agent_output)

    assert len(institution.persons) == 2
    persons_list = list(institution.persons)
    assert any(p.first_name == "John" and p.last_name == "Doe" for p in persons_list)
    assert any(p.first_name == "Jane" and p.last_name == "Smith" for p in persons_list)


def test_updating_existing_person_contact_info():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # First update with initial data
    agent_output_1 = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john.old@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
        ]
    )
    institution.update_persons_from_agent(agent_output_1)

    # Second update with same person but new contact info
    agent_output_2 = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john.new@example.com", "+1-555-9999", "https://techcorp.com/team/john"),
        ]
    )
    institution.update_persons_from_agent(agent_output_2)

    # Should still have only 1 person (not duplicated)
    assert len(institution.persons) == 1

    # But contact info should be updated
    john = list(institution.persons)[0]
    assert john.email == "john.new@example.com"
    assert john.phone == "+1-555-9999"


def test_adding_new_persons_while_keeping_existing():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # First update
    agent_output_1 = model.AgentOutput(
        persons=[
            model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
        ]
    )
    institution.update_persons_from_agent(agent_output_1)

    # Second update with a different person
    agent_output_2 = model.AgentOutput(
        persons=[
            model.AgentPerson("Jane", "Smith", "jane@example.com", "+1-555-0101", "https://techcorp.com/team/jane"),
        ]
    )
    institution.update_persons_from_agent(agent_output_2)

    # Should have both persons (add/update logic, not replace)
    assert len(institution.persons) == 2
    persons_list = list(institution.persons)
    assert any(p.first_name == "John" for p in persons_list)
    assert any(p.first_name == "Jane" for p in persons_list)


def test_multiple_updates_preserve_history():
    institution = model.Institution("TechCorp", "Technology", "https://techcorp.com")

    # Update 1: Add John
    institution.update_persons_from_agent(
        model.AgentOutput([
            model.AgentPerson("John", "Doe", "john@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
        ])
    )

    # Update 2: Add Jane, update John's email
    institution.update_persons_from_agent(
        model.AgentOutput([
            model.AgentPerson("John", "Doe", "john.new@example.com", "+1-555-0100", "https://techcorp.com/team/john"),
            model.AgentPerson("Jane", "Smith", "jane@example.com", "+1-555-0101", "https://techcorp.com/team/jane"),
        ])
    )

    # Update 3: Add Bob (John and Jane still exist)
    institution.update_persons_from_agent(
        model.AgentOutput([
            model.AgentPerson("Bob", "Johnson", "bob@example.com", "+1-555-0102", "https://techcorp.com/team/bob"),
        ])
    )

    # Should have all 3 persons
    assert len(institution.persons) == 3
    persons_list = list(institution.persons)

    # Verify all three exist
    john = next(p for p in persons_list if p.first_name == "John")
    jane = next(p for p in persons_list if p.first_name == "Jane")
    bob = next(p for p in persons_list if p.first_name == "Bob")

    # John's email should be updated from update 2
    assert john.email == "john.new@example.com"
    assert jane.email == "jane@example.com"
    assert bob.email == "bob@example.com"


def test_person_equality_based_on_natural_key():
    person1 = model.Person("John", "Doe", "https://example.com/john", "john1@example.com", "+1-555-0100")
    person2 = model.Person("John", "Doe", "https://example.com/john", "john2@example.com", "+1-555-9999")
    person3 = model.Person("Jane", "Doe", "https://example.com/john", "jane@example.com", "+1-555-0101")

    # Same first_name, last_name, source_url = equal
    assert person1 == person2

    # Different first_name = not equal
    assert person1 != person3

    # Can be used in sets
    person_set = {person1, person2, person3}
    assert len(person_set) == 2  # person1 and person2 are duplicates


def test_person_update_contact_info():
    person = model.Person("John", "Doe", "https://example.com/john", "old@example.com", "+1-555-0100", "CEO")

    person.update_contact_info("new@example.com", "+1-555-9999", "CTO")

    assert person.email == "new@example.com"
    assert person.phone == "+1-555-9999"
    assert person.job_title == "CTO"

    # Natural key should not change
    assert person.first_name == "John"
    assert person.last_name == "Doe"
    assert person.source_url == "https://example.com/john"
