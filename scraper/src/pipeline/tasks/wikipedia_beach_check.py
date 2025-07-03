import requests
from bs4 import BeautifulSoup
from prefect import task

andalusian_provinces = {
    "Almería",
    "Cádiz",
    "Córdoba",
    "Granada",
    "Huelva",
    "Jaén",
    "Málaga",
    "Sevilla",
}


@task
def get_towns_with_beaches_from_wikipedia(
    url="https://es.wikipedia.org/wiki/Anexo:Playas_de_Andaluc%C3%ADa",
) -> list[str]:
    """
    Fetches a list of towns in Andalusia, Spain, that have beaches by scraping the relevant Wikipedia page.
    Returns:
        List[str]: A list with towns with beaches
    Notes:
        - The function fetches and parses the Wikipedia page "Anexo:Playas_de_Andalucía".
        - Only towns listed under recognized Andalusian provinces are included.
        - Requires the variables `andalusian_provinces` and `BeautifulSoup` to be defined/imported in the scope.
    """

    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    towns = []
    current_province = None

    for tag in soup.find_all(["h2", "ul"]):
        if tag.name == "h2":
            span = tag.find("span", id=True)
            if span:
                header = tag.get_text().split("[")[0].strip()
                if header in andalusian_provinces:
                    current_province = header
                else:
                    current_province = None

        elif tag.name == "ul" and current_province:
            for li in tag.find_all("li"):
                link = li.find("a")
                if link:
                    town = link.text.strip()
                    if town and town not in towns:
                        towns.append(town)

    return towns
