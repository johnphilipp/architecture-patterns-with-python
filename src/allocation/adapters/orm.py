from sqlalchemy import Table, MetaData, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, registry

from allocation.domain import model


metadata = MetaData()

# Create a registry
mapper_registry = registry()

institutions = Table(
    "institutions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255)),
    Column("industry", String(255)),
    Column("website", String(255)),
    Column("uid", String(12)),
    Column("handelsregister_url", String(255)),
)

persons = Table(
    "persons",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("institution_id", ForeignKey("institutions.id")),
    Column("first_name", String(255)),
    Column("last_name", String(255)),
)

person_details = Table(
    "person_details",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("person_id", ForeignKey("persons.id")),
    Column("job_title", String(255), nullable=False),
    Column("email", String(255)),
    Column("phone", String(255)),
    Column("source_url", String(255), nullable=False),
)


def start_mappers():
    # Map PersonDetail first
    person_details_mapper = mapper_registry.map_imperatively(
        model.PersonDetail,
        person_details
    )

    # Map Person with relationship to PersonDetail
    persons_mapper = mapper_registry.map_imperatively(
        model.Person,
        persons,
        properties={
            "_person_details": relationship(
                person_details_mapper,
                collection_class=set,
            )
        },
    )

    # Map Institution with relationship to Person
    mapper_registry.map_imperatively(
        model.Institution,
        institutions,
        properties={
            "_persons": relationship(
                persons_mapper,
                collection_class=set,
            )
        },
    )
