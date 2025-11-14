from __future__ import annotations
from sqlalchemy.exc import NoResultFound

from allocation.domain import model
from allocation.service_layer import unit_of_work
from allocation.adapters.agent import AbstractAgent


def add_institution(
    name: str,
    industry: str,
    website: str,
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        institution = model.Institution(name, industry, website)
        uow.institutions.add(institution)
        uow.commit()


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