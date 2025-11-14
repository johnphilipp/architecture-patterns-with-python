"""
Agent infrastructure service for fetching persons from institution websites.
"""
import abc
from allocation.domain import model


class AbstractAgent(abc.ABC):
    @abc.abstractmethod
    def fetch_persons(self, agent_input: model.AgentInput) -> model.AgentOutput:
        raise NotImplementedError


class FakeAgent(AbstractAgent):
    """
    Mock/stub implementation of Agent that returns hardcoded test data.
    Used for testing and demo purposes.
    """

    def fetch_persons(self, agent_input: model.AgentInput) -> model.AgentOutput:
        """
        Returns hardcoded sample persons based on the institution.
        In a real implementation, this would scrape the website.
        """
        # Generate some fake persons for demo purposes
        persons = [
            model.AgentPerson(
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                phone="+1-555-0100",
                source_url=f"{agent_input.website}/about/team/john-doe",
            ),
            model.AgentPerson(
                first_name="Jane",
                last_name="Smith",
                email="jane.smith@example.com",
                phone="+1-555-0101",
                source_url=f"{agent_input.website}/about/team/jane-smith",
            ),
            model.AgentPerson(
                first_name="Bob",
                last_name="Johnson",
                email="bob.johnson@example.com",
                phone="+1-555-0102",
                source_url=f"{agent_input.website}/about/leadership/bob-johnson",
            ),
        ]

        return model.AgentOutput(persons=persons)