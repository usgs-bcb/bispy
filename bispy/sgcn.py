import requests
from datetime import datetime


class Search:
    def __init__(self):
        self.sgcn_spp_search_api = "https://sciencebase.usgs.gov/staging/bis/api/v1/swap/nationallist"

    def search(self, name):
        record = {
            "search_api": f"{self.sgcn_spp_search_api}?scientificname={name}",
            "search_date": datetime.utcnow().isoformat()
        }

        r_search = requests.get(record["search_api"]).json()
        record["sgcn_species"] = next((i["_source"]["properties"] for i in r_search["hits"]["hits"]
                                       if i["_source"]["properties"]["scientificname"] == name), None)

        return record
