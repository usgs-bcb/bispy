import requests
import os
import re
from . import bis

bis_utils = bis.Utils()

class Iucn:
    def __init__(self):
        self.iucn_api_base = "http://apiv3.iucnredlist.org/api/v3"
        self.iucn_species_api = f"{self.iucn_api_base}/species"
        self.iucn_threats_api = f"{self.iucn_api_base}/threats/species/id"
        self.iucn_habitats_api = f"{self.iucn_api_base}/habitats/species/id"
        self.iucn_measures_api = f"{self.iucn_api_base}/measures/species/id"
        self.iucn_citation_api = f"{self.iucn_api_base}/species/citation/id"
        self.response_result = bis_utils.processing_metadata()

        self.iucn_categories = {
            "NE": "Not Evaluated",
            "DD": "Data Deficient",
            "LC": "Least Concern",
            "NT": "Near Threatened",
            "VU": "Vulnerable",
            "EN": "Endangered",
            "CR": "Critically Endangered",
            "EW": "Extinct in the Wild",
            "EX": "Extinct",
            "LR/lc": "Least Concern (in review)",
            "LR/nt": "Near Threatened (in review)",
            "LR/cd": "Not Categorized (in review)"
        }

    def search_species(self, scientificname, name_source=None):
        iucn_result = self.response_result
        iucn_result["Processing Metadata"]["Summary Result"] = "Not Matched"
        iucn_result["Processing Metadata"]["Scientific Name"] = scientificname
        iucn_result["Processing Metadata"]["Name Source"] = name_source
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

        iucn_species_data = iucn_response.json()

        if "result" not in iucn_species_data.keys() or len(iucn_species_data["result"]) == 0:
            iucn_result["Processing Metadata"]["Summary Result"] = "Species Name Not Found"
            iucn_result["Processing Metadata"]["Status"] = "failure"
            return iucn_result

        iucn_result["Processing Metadata"]["Summary Result"] = "Species Name Matched"
        iucn_result["Processing Metadata"]["Status"] = "success"

        iucn_citation_response = requests.get(
            f"{self.iucn_citation_api}/{iucn_species_data['result'][0]['taxonid']}?token={os.environ['token_iucn']}"
        ).json()

        iucn_citation_string = iucn_citation_response["result"][0]["citation"]
        iucn_doi = re.search('http://dx.doi.org/10.2305/(.+?).en', iucn_citation_string)
        if iucn_doi:
            iucn_doi_link = f"http://dx.doi.org/10.2305/{iucn_doi.group(1)}.en"

        iucn_result["IUCN Species Summary"] = {
            "Taxon ID": iucn_species_data['result'][0]['taxonid'],
            "Citation": iucn_citation_string,
            "Report Link": iucn_doi_link,
            "Status Code": iucn_species_data['result'][0]['category'],
            "Status": self.iucn_categories[iucn_species_data['result'][0]['category']],
            "Assessment Date": iucn_species_data['result'][0]['assessment_date'],
            "Population Trend": iucn_species_data['result'][0]['population_trend'],
        }

        return iucn_result

