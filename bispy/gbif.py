import requests
from datetime import datetime
from . import bis

bis_utils = bis.Utils()


class Gbif:
    def __init__(self):
        self.response_result = bis_utils.processing_metadata()
        self.gbif_spp_occ_summary_api = "https://api.gbif.org/v1/occurrence/search?country=US&limit=0&facet=institutionCode&facet=year&facet=basisOfRecord&{}={}"
        self.gbif_species_suggest_stub = "https://api.gbif.org/v1/species/suggest?q={}"

    def summarize_us_species(self, scientificname, name_source=None):
        result = self.response_result
        result["Processing Metadata"]["Summary Result"] = "Not Matched"
        result["Processing Metadata"]["Scientific Name"] = scientificname
        result["Processing Metadata"]["Name Source"] = name_source
        result["Processing Metadata"]["Search URL"] = self.gbif_species_suggest_stub.format(scientificname)
        result["Processing Metadata"]["API"] = list()

        gbif_spp_search_results = requests.get(self.gbif_species_suggest_stub.format(scientificname)).json()

        if len(gbif_spp_search_results) == 0:
            result["Processing Metadata"]["Status"] = "failure"
            return result

        result["GBIF Species Record"] = gbif_spp_search_results[0]

        if "nubKey" in result["GBIF Species Record"].keys():
            result["Processing Metadata"]["API"].append(
                self.gbif_spp_occ_summary_api.format(
                    "taxon-Key",
                    result["GBIF Species Record"]["nubKey"]
                )
            )
        else:
            result["Processing Metadata"]["API"].append(
                self.gbif_spp_occ_summary_api.format(
                    "scientificName",
                    scientificname
                )
            )

        gbif_occ_results = requests.get(
            result["Processing Metadata"]["API"][-1]
        ).json()

        for key in ["endOfRecords", "limit", "offset", "results"]:
            del gbif_occ_results[key]

        result["Processing Metadata"]["Summary Result"] = "Matched"
        result["Processing Metadata"]["Status"] = "success"
        result["Occurrence Summary"] = gbif_occ_results

        return result

