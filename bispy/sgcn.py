import requests
from datetime import datetime


class Search:
    def __init__(self):
        self.sgcn_spp_search_api = "https://sciencebase.usgs.gov/staging/bis/api/v1/swap/nationallist"

    def search(self, name):
        record = {
            "search_api": f"{self.sgcn_spp_search_api}?scientificname={name}",
            "search_date": datetime.utcnow().isoformat(),
            "results": list()
        }

        r_search = requests.get(record["search_api"]).json()

        record["search_results"] = len(r_search["hits"]["hits"])

        for hit in r_search["hits"]["hits"]:
            record["results"].append(hit["_source"]["properties"])

        return record
