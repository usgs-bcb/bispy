import requests
import os
import bis


class Iucn:
    def __init__(self):
        self.iucn_api_base = "http://apiv3.iucnredlist.org/api/v3"
        self.iucn_species_api = f"{self.iucn_api_base}/species"
        self.response_result = bis.response_result()

    def search_species(self, scientificname):
        iucn_result = self.response_result
        iucn_result["Processing Metadata"]["Summary Result"] = "Not Matched"
        iucn_result["Processing Metadata"]["Search URL"] = f"{self.iucn_species_api}/{scientificname}"

        if "token_iucn" not in os.environ:
            iucn_result["Processing Metadata"]["Summary Result"] = "API token not present to run IUCN Red List query"
            return iucn_result

        iucn_response = requests.get(
            f'{iucn_result["Processing Metadata"]["Search URL"]}?token={os.environ["token_iucn"]}'
        )

        if iucn_response.status_code != 200:
            iucn_result["Processing Metadata"]["Summary Result"] = "IUCN API returned an unprocessable result"
            return iucn_result

        iucn_result["IUCN Species"] = iucn_response.json()

        return iucn_result

