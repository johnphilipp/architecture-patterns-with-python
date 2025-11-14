from flask import Flask, request

from allocation.domain import model
from allocation.adapters import orm, agent, handelsregister
from allocation.service_layer import services, unit_of_work

app = Flask(__name__)
orm.start_mappers()

# Instantiate services for dependency injection
fake_agent = agent.FakeAgent()
fake_handelsregister = handelsregister.FakeHandelsregister()


@app.route("/add_institution", methods=["POST"])
def add_institution():
    institution_id = services.add_institution(
        request.json["name"],
        request.json["industry"],
        request.json["website"],
        unit_of_work.SqlAlchemyUnitOfWork(),
        request.json.get("uid", ""),
        request.json.get("handelsregister_url", ""),
    )
    return {"id": institution_id}, 201


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


@app.route("/update_from_handelsregister", methods=["POST"])
def update_from_handelsregister():
    try:
        services.update_from_handelsregister(
            request.json["institution_id"],
            unit_of_work.SqlAlchemyUnitOfWork(),
            fake_handelsregister,
        )
    except model.InstitutionNotFound as e:
        return {"message": str(e)}, 404
    except model.HandelsregisterUrlMissing as e:
        return {"message": str(e)}, 400

    return "OK", 200
