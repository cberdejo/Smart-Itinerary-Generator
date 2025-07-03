import requests
from prefect import task

province_identifiers = {
    4: "Almería",
    11: "Cádiz",
    14: "Córdoba",
    18: "Granada",
    21: "Huelva",
    23: "Jaén",
    29: "Málaga",
    41: "Sevilla",
}


@task
def get_municipios_name_and_ubi() -> list:
    """
    Fetches municipalities from Junta de Andalucía API and filters them by province identifiers.
    Returns:
        list: A list of dictionaries containing municipality information.
    """
    url = "https://datos.juntadeandalucia.es/api/v0/municipalities/all?format=json"

    response = requests.get(url, headers={"Accept": "application/json"})

    if response.status_code == 200:
        data = response.json()
        andalusian_towns = []

        for item in data:
            province_id = item.get("province_identifier")
            if province_id in province_identifiers:
                try:
                    lat = float(item["latitude"].replace(",", "."))
                    lon = float(item["longitude"].replace(",", "."))
                except (ValueError, AttributeError):
                    continue

                town = {
                    "municipality_name": item.get("municipality_name"),
                    "municipality_ine": item.get("municipality_ine"),
                    "capital_city": item.get("capital_city"),
                    "latitude": lat,
                    "longitude": lon,
                    "identifier": item.get("identifier"),
                    "province_identifier": province_id,
                    "province_name": province_identifiers[province_id],
                }

                andalusian_towns.append(town)

        return andalusian_towns
    else:
        response.raise_for_status()
