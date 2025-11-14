from flask import Flask, request

from allocation.domain import model
from allocation.adapters import orm, agent
from allocation.service_layer import services, unit_of_work

app = Flask(__name__)
orm.start_mappers()

# Instantiate the agent for dependency injection
fake_agent = agent.FakeAgent()


@app.route("/add_institution", methods=["POST"])
def add_institution():
    services.add_institution(
        request.json["name"],
        request.json["industry"],
        request.json["website"],
        unit_of_work.SqlAlchemyUnitOfWork(),
    )
    return "OK", 201


@app.route("/update_from_website", methods=["POST"])
def update_from_website():
    try:
        services.update_from_website(
            request.json["institution_id"],
            unit_of_work.SqlAlchemyUnitOfWork(),
            fake_agent,
        )
    except model.InstitutionNotFound as e:
        return {"message": str(e)}, 404

    return "OK", 200