from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Set


class InstitutionNotFound(Exception):
    pass


# DTOs
@dataclass
class AgentInput:
    name: str
    industry: str
    website: str


@dataclass
class AgentPerson:
    first_name: str
    last_name: str
    email: str
    phone: str
    source_url: str


@dataclass
class AgentOutput:
    persons: List[AgentPerson]


# Domain Models
class Person:
    """
    Person entity - contained within Institution aggregate.
    Identity is based on database ID, but __eq__/__hash__ use natural key
    for set membership and matching logic.
    """

    def __init__(
        self,
        first_name: str,
        last_name: str,
        source_url: str,
        email: str = "",
        phone: str = "",
        job_title: str = "",
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.source_url = source_url
        self.email = email
        self.phone = phone
        self.job_title = job_title

    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return (
            self.first_name == other.first_name
            and self.last_name == other.last_name
            and self.source_url == other.source_url
        )

    def __hash__(self):
        return hash((self.first_name, self.last_name, self.source_url))

    def __repr__(self):
        return f"<Person {self.first_name} {self.last_name}>"

    def update_contact_info(
        self,
        email: str,
        phone: str,
        job_title: str,
    ):
        """Update mutable contact information"""
        self.email = email
        self.phone = phone
        self.job_title = job_title


class Institution:
    """
    Institution aggregate root.
    Contains a set of Person entities.
    """

    def __init__(
        self,
        name: str,
        industry: str,
        website: str,
    ):
        self.name = name
        self.industry = industry
        self.website = website
        self._persons = set()  # type: Set[Person]

    def __repr__(self):
        return f"<Institution {self.name}>"

    @property
    def persons(self) -> Set[Person]:
        """Read-only access to persons set"""
        return self._persons.copy()

    def update_persons_from_agent(self, agent_output: AgentOutput):
        """
        Update persons from agent output using add/update logic.
        - If person exists (matched by natural key): update contact info
        - If person is new: add to set
        - Keep existing persons not in output (accumulate over time)
        """
        for agent_person in agent_output.persons:
            # Create a Person instance for matching
            new_person = Person(
                first_name=agent_person.first_name,
                last_name=agent_person.last_name,
                source_url=agent_person.source_url,
                email=agent_person.email,
                phone=agent_person.phone,
                job_title="",  # AgentPerson doesn't have job_title in spec
            )

            # Check if person already exists in our set
            existing_person = self._find_person(new_person)

            if existing_person:
                # Update existing person's contact info
                existing_person.update_contact_info(
                    email=agent_person.email,
                    phone=agent_person.phone,
                    job_title="",  # AgentPerson doesn't have job_title
                )
            else:
                # Add new person to set
                self._persons.add(new_person)

    def _find_person(self, person: Person) -> Optional[Person]:
        """Find a person in the set using natural key equality"""
        for p in self._persons:
            if p == person:  # Uses __eq__ based on natural key
                return p
        return None
