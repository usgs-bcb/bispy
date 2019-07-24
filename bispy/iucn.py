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
        self.iucn_resolvable_id_base = "https://www.iucnredlist.org/species/"
        self.doi_pattern_start = "http://dx.doi.org"
        self.doi_pattern_end = ".en"
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
        iucn_result["processing_metadata"]["api"] = f"{self.iucn_species_api}/{scientificname}"
        iucn_result["parameters"] = {
            "Scientific Name": scientificname,
            "Name Source": name_source
        }

        if "token_iucn" not in os.environ:
            iucn_result["processing_metadata"]["status"] = "error"
            iucn_result["processing_metadata"]["status_message"] = "API token not present to run IUCN Red List query"
            return iucn_result

        iucn_response = requests.get(
            f'{iucn_result["processing_metadata"]["api"]}?token={os.environ["token_iucn"]}'
        )

        if iucn_response.status_code != 200:
            iucn_result["processing_metadata"]["status"] = "error"
            iucn_result["processing_metadata"]["status_message"] = "IUCN API returned an unprocessable result"
            return iucn_result

        iucn_species_data = iucn_response.json()

        if "result" not in iucn_species_data.keys() or len(iucn_species_data["result"]) == 0:
            iucn_result["processing_metadata"]["status"] = "failure"
            iucn_result["processing_metadata"]["status_message"] = "Species Name Not Found"
            return iucn_result

        iucn_result["processing_metadata"]["status"] = "success"
        iucn_result["processing_metadata"]["status_message"] = "Species Name Matched"

        iucn_result["iucn_species_summary"] = {
            "iucn_taxonid": iucn_species_data['result'][0]['taxonid'],
            "iucn_status_code": iucn_species_data['result'][0]['category'],
            "iucn_status_name": self.iucn_categories[iucn_species_data['result'][0]['category']],
            "record_date": iucn_species_data['result'][0]['assessment_date'],
            "iucn_population_trend": iucn_species_data['result'][0]['population_trend'],
        }

        iucn_citation_response = requests.get(
            f"{self.iucn_citation_api}/{iucn_result['iucn_species_summary']['iucn_taxonid']}?token={os.environ['token_iucn']}"
        ).json()

        iucn_result["iucn_species_summary"]["citation_string"] = iucn_citation_response["result"][0]["citation"]

        regex_string_secondary_id = f"e\.T{iucn_result['iucn_species_summary']['iucn_taxonid']}A(.*?)\."
        match_secondary_id = re.search(regex_string_secondary_id,
                                              iucn_result["iucn_species_summary"]["citation_string"])
        if match_secondary_id is not None:
            iucn_result["iucn_species_summary"]["iucn_secondary_identifier"] = match_secondary_id.group(1)
            iucn_result["iucn_species_summary"]["resolvable_identifier"] = \
                f"{self.iucn_resolvable_id_base}" \
                f"{iucn_result['iucn_species_summary']['iucn_taxonid']}/" \
                f"{match_secondary_id.group(1)}"
        else:
            iucn_result["iucn_species_summary"]["iucn_secondary_identifier"] = None
            iucn_result["iucn_species_summary"]["resolvable_identifier"] = None

        regex_string_doi = f"{self.doi_pattern_start}(.*?){self.doi_pattern_end}"
        match_iucn_doi = re.search(regex_string_doi, iucn_result["iucn_species_summary"]["citation_string"])

        if match_iucn_doi is not None:
            iucn_result["iucn_species_summary"]["doi"] = f"{self.doi_pattern_start}{match_iucn_doi.group(1)}{self.doi_pattern_end}"
        else:
            iucn_result["iucn_species_summary"]["doi"] = None

        return iucn_result

