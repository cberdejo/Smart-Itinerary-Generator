# All code/comments in English
from app.models.generic_response import GenericResponse
from app.models.municiaplity import TownOut
from app.models.itinerary import Itinerary
from app.models.db_models import Town, Image, RealEstate, Intangible
import json


def test_generic_response_to_json():
    gr = GenericResponse(code=200, message="ok", data={"x": 1})
    res = gr.to_json_response()
    assert res.status_code == 200

    body = json.loads(res.body)
    assert body["data"]["x"] == 1
    assert body["message"] == "ok"
    assert body["code"] == 200


def test_townout_from_sqlmodel_instance():
    town = Town(
        municipality_ine="0000",
        municipality_name="Foo",
        description=None,
        history=None,
        capital_city=False,
        latitude=1.0,
        longitude=2.0,
        province_identifier="P",
        province_name="Prov",
        has_beach=True,
        images=[Image(url="img.jpg", municipality_ine="0000")],
        real_estate_assets=[
            RealEstate(name="Castle", municipality_ine="0000", typologies=[])
        ],
        intangible_assets=[Intangible(name="Festival", municipality_ine="0000")],
    )

    out = TownOut.model_validate(town)
    assert out.municipality_ine == "0000"
    assert out.images[0].url == "img.jpg"
    assert out.real_estate_assets[0].name == "Castle"
    assert out.intangible_assets[0].name == "Festival"


# All code/comments in English
import pytest
from pydantic import ValidationError
from app.models.form_response import FormResponse, Location


def test_empty_strings_are_none():
    data = {
        "beach": "",
        "location": "",
        "travelTimeLimit": "",
        "culturalInfluences": "",
        "environment": "",
        "historicalPeriods": "",
        "monuments": "",
        "traditions": "",
        "travelInterests": "",
        "villageType": "",
    }
    model = FormResponse(**data)
    assert model.beach == "indiference"
    assert model.travelTimeLimit is None
    assert model.environment is None
    assert model.culturalInfluences is None
    assert model.historicalPeriods is None
    assert model.monuments is None
    assert model.traditions is None
    assert model.travelInterests is None
    assert model.villageType is None
    assert model.get_embedding_text() == ""


def test_travel_time_limit_string_to_int():
    model = FormResponse(
        beach="yes",
        location=None,
        travelTimeLimit="45",
        culturalInfluences=None,
        environment=None,
        historicalPeriods=None,
        monuments=None,
        traditions=None,
        travelInterests=None,
        villageType=None,
    )
    assert model.travelTimeLimit == 45


def test_travel_time_limit_invalid_raises():
    with pytest.raises(ValidationError):
        FormResponse(
            beach="no",
            location=None,
            travelTimeLimit="forty",
            culturalInfluences=None,
            environment=None,
            historicalPeriods=None,
            monuments=None,
            traditions=None,
            travelInterests=None,
            villageType=None,
        )


def test_get_embedding_text_builds_phrase():
    model = FormResponse(
        beach="yes",
        location=Location(lat=36.7, lng=-4.4, label="Málaga"),
        travelTimeLimit=60,
        culturalInfluences="árabe",
        environment="montaña",
        historicalPeriods="romana",
        monuments="castillos",
        traditions="ferias",
        travelInterests="gastronomía",
        villageType="pueblo blanco",
    )
    text = model.get_embedding_text()
    assert "pueblo blanco" in text
    assert "Interesado en monumentos" in text
    assert "gastronomía" in text
    assert "romana" in text
    assert "ferias" in text
    assert "montaña" in text
    assert "árabe" in text
