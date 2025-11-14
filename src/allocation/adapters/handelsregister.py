"""
Handelsregister infrastructure service for fetching persons from Swiss government website.
"""
import abc
from allocation.domain import model


class AbstractHandelsregister(abc.ABC):
    @abc.abstractmethod
    def fetch_persons(self, handelsregister_input: model.HandelsregisterInput) -> model.HandelsregisterOutput:
        raise NotImplementedError


class FakeHandelsregister(AbstractHandelsregister):
    """
    Mock/stub implementation of Handelsregister that returns hardcoded test data.
    Used for testing and demo purposes.
    """

    def fetch_persons(self, handelsregister_input: model.HandelsregisterInput) -> model.HandelsregisterOutput:
        """
        Returns hardcoded sample persons from Handelsregister.
        In a real implementation, this would scrape the government website.

        Note: Handelsregister provides full_name (not separated) and job_title.
        No email or phone information available.
        """
        # Generate some fake persons with Swiss-style names
        persons = [
            model.HandelsregisterPerson(
                full_name="Max Hans Müller",
                job_title="Geschäftsführer",
            ),
            model.HandelsregisterPerson(
                full_name="Anna Maria Schneider",
                job_title="Verwaltungsrätin",
            ),
            model.HandelsregisterPerson(
                full_name="Peter Schmidt",
                job_title="Prokurist",
            ),
        ]

        return model.HandelsregisterOutput(persons=persons)