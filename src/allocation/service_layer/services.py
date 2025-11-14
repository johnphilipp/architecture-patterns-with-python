from __future__ import annotations
from sqlalchemy.exc import NoResultFound

from allocation.domain import model
from allocation.service_layer import unit_of_work
from allocation.adapters.agent import AbstractAgent
from allocation.adapters.handelsregister import AbstractHandelsregister


def add_institution(
    name: str,
    industry: str,
    website: str,
    uow: unit_of_work.AbstractUnitOfWork,
    uid: str = "",
    handelsregister_url: str = "",
) -> int:
    with uow:
        institution = model.Institution(name, industry, website, uid, handelsregister_url)
        uow.institutions.add(institution)
        uow.commit()
        return institution.id


def update_from_website(
    institution_id: int,
    uow: unit_of_work.AbstractUnitOfWork,
    agent: AbstractAgent,
):
    with uow:
        try:
            institution = uow.institutions.get(institution_id)
        except NoResultFound:
            raise model.InstitutionNotFound(f"Institution with id {institution_id} not found")

        # Create agent input from institution
        agent_input = model.AgentInput(
            name=institution.name,
            industry=institution.industry,
            website=institution.website,
        )

        # Fetch persons from agent
        agent_output = agent.fetch_persons(agent_input)

        # Update institution with agent output
        institution.update_persons_from_agent(agent_output)

        uow.commit()


def update_from_handelsregister(
    institution_id: int,
    uow: unit_of_work.AbstractUnitOfWork,
    handelsregister: AbstractHandelsregister,
):
    with uow:
        try:
            institution = uow.institutions.get(institution_id)
        except NoResultFound:
            raise model.InstitutionNotFound(f"Institution with id {institution_id} not found")

        # Check if handelsregister_url is available
        if not institution.handelsregister_url:
            raise model.HandelsregisterUrlMissing(
                f"Institution {institution_id} does not have a handelsregister_url"
            )

        # Create handelsregister input
        hr_input = model.HandelsregisterInput(
            handelsregister_url=institution.handelsregister_url
        )

        # Fetch persons from Handelsregister
        hr_output = handelsregister.fetch_persons(hr_input)

        # Update institution with Handelsregister output
        institution.update_persons_from_handelsregister(hr_output)

        uow.commit()