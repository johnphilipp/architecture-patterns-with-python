from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Set


class InstitutionNotFound(Exception):
    pass


class HandelsregisterUrlMissing(Exception):
    pass


# Agent DTOs (existing)
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


# Handelsregister DTOs (new)
@dataclass
class HandelsregisterInput:
    handelsregister_url: str


@dataclass
class HandelsregisterPerson:
    full_name: str  # e.g., "John Michael Doe"
    job_title: str


@dataclass
class HandelsregisterOutput:
    persons: List[HandelsregisterPerson]


# Domain Models
class PersonDetail:
    """
    PersonDetail entity - represents contact details from a specific source.
    Part of Person aggregate. Equality based on source_url.
    """

    def __init__(
        self,
        job_title: str,
        source_url: str,
        email: str = "",
        phone: str = "",
    ):
        self.job_title = job_title
        self.source_url = source_url
        self.email = email
        self.phone = phone

    def __eq__(self, other):
        if not isinstance(other, PersonDetail):
            return False
        return self.source_url == other.source_url

    def __hash__(self):
        return hash(self.source_url)

    def __repr__(self):
        return f"<PersonDetail from {self.source_url}>"

    def update(self, job_title: str, email: str, phone: str):
        """Update mutable fields of this detail"""
        self.job_title = job_title
        self.email = email
        self.phone = phone


class Person:
    """
    Person entity - contained within Institution aggregate.
    Identity based on (first_name, last_name) only.
    Contains multiple PersonDetail entities from different sources.
    """

    def __init__(
        self,
        first_name: str,
        last_name: str,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self._person_details = set()  # type: Set[PersonDetail]

    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return (
            self.first_name == other.first_name
            and self.last_name == other.last_name
        )

    def __hash__(self):
        return hash((self.first_name, self.last_name))

    def __repr__(self):
        return f"<Person {self.first_name} {self.last_name}>"

    @property
    def person_details(self) -> Set[PersonDetail]:
        """Read-only access to person details set"""
        return self._person_details.copy()

    def add_or_update_detail(self, detail: PersonDetail):
        """
        Add a new detail or update existing one based on source_url.
        If a detail with the same source_url exists, update it.
        Otherwise, add the new detail.
        """
        existing_detail = self._find_detail(detail.source_url)
        if existing_detail:
            # Update existing detail
            existing_detail.update(detail.job_title, detail.email, detail.phone)
        else:
            # Add new detail
            self._person_details.add(detail)

    def _find_detail(self, source_url: str) -> Optional[PersonDetail]:
        """Find a detail by source_url"""
        for detail in self._person_details:
            if detail.source_url == source_url:
                return detail
        return None


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
        uid: str = "",
        handelsregister_url: str = "",
    ):
        self.name = name
        self.industry = industry
        self.website = website
        self.uid = uid
        self.handelsregister_url = handelsregister_url
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
        - Find or create Person by (first_name, last_name)
        - Create PersonDetail from AgentPerson
        - Add or update the detail on the person
        """
        for agent_person in agent_output.persons:
            # Find or create person
            person = self._find_or_create_person(
                agent_person.first_name,
                agent_person.last_name
            )

            # Create detail from agent data
            detail = PersonDetail(
                job_title="",  # AgentPerson doesn't have job_title
                source_url=agent_person.source_url,
                email=agent_person.email,
                phone=agent_person.phone,
            )

            # Add or update detail
            person.add_or_update_detail(detail)

    def update_persons_from_handelsregister(self, handelsregister_output: HandelsregisterOutput):
        """
        Update persons from Handelsregister output.
        - Parse full_name into first_name and last_name (last word = last_name)
        - Find or create Person by (first_name, last_name)
        - Create PersonDetail from HandelsregisterPerson
        - Add or update the detail on the person
        """
        for hr_person in handelsregister_output.persons:
            # Parse full name
            first_name, last_name = self._parse_full_name(hr_person.full_name)

            # Find or create person
            person = self._find_or_create_person(first_name, last_name)

            # Create detail from Handelsregister data
            # Use handelsregister_url as base for source_url
            source_url = f"{self.handelsregister_url}/person/{first_name}-{last_name}"
            detail = PersonDetail(
                job_title=hr_person.job_title,
                source_url=source_url,
                email="",  # Handelsregister doesn't provide email
                phone="",  # Handelsregister doesn't provide phone
            )

            # Add or update detail
            person.add_or_update_detail(detail)

    def _find_or_create_person(self, first_name: str, last_name: str) -> Person:
        """Find existing person by name, or create new one if not found"""
        # Create a temporary Person for searching
        search_person = Person(first_name, last_name)

        # Try to find existing person
        for p in self._persons:
            if p == search_person:  # Uses __eq__ based on (first_name, last_name)
                return p

        # Person not found, create and add new one
        new_person = Person(first_name, last_name)
        self._persons.add(new_person)
        return new_person

    def _parse_full_name(self, full_name: str) -> tuple[str, str]:
        """
        Parse full name into first_name and last_name.
        Last word = last_name, everything before = first_name.
        E.g., "John Michael Doe" → ("John Michael", "Doe")
        """
        parts = full_name.strip().split()
        if len(parts) == 0:
            return "", ""
        elif len(parts) == 1:
            return parts[0], ""
        else:
            last_name = parts[-1]
            first_name = " ".join(parts[:-1])
            return first_name, last_name
