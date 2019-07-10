import requests
from datetime import datetime
from . import bis

bis_utils = bis.Utils()


class Search:
    def __init__(self):
        self.description = "Set of functions for searching the Species of Greatest Conservation Need API"
        self.sgcn_spp_search_api = "https://sciencebase.usgs.gov/staging/bis/api/v1/swap/nationallist"
        self.response_result = bis_utils.processing_metadata()

    def search(self, scientificname, name_source=None):
        result = self.response_result
        result["Processing Metadata"]["Summary Result"] = "Not Matched"
        result["Processing Metadata"]["Status"] = "failure"
        result["Processing Metadata"]["Scientific Name"] = scientificname
        result["Processing Metadata"]["Name Source"] = name_source
        result["Processing Metadata"]["Search URL"] = f"{self.sgcn_spp_search_api}?scientificname={scientificname}"

        r_search = requests.get(result["Processing Metadata"]["Search URL"]).json()
        sgcn_species = next((i["_source"]["properties"] for i in r_search["hits"]["hits"]
                                       if i["_source"]["properties"]["scientificname"] == scientificname), None)

        if sgcn_species is not None:
            result["Processing Metadata"]["Summary Result"] = "Name Match"
            result["Processing Metadata"]["Status"] = "success"
            result["SGCN Species"] = sgcn_species

        return result
