import requests
from datetime import datetime
from . import bis

bis_utils = bis.Utils()


class Gbif:
    def __init__(self):
        self.response_result = bis_utils.processing_metadata()
        self.gbif_spp_occ_summary_api = "https://api.gbif.org/v1/occurrence/search?country=US&limit=0&facet=institutionCode&facet=year&facet=basisOfRecord&{}={}"
        self.gbif_species_suggest_stub = "https://api.gbif.org/v1/species/suggest?q={}"

    def summarize_us_species(self, scientific_name):
        gbif_spp_search_results = requests.get(self.gbif_species_suggest_stub.format(scientific_name)).json()

        if len(gbif_spp_search_results) == 0:
            return None

        species_summary = {
            "Processing Metadata": {
                "Date Processed": datetime.utcnow().isoformat(),
                "Scientific Name": scientific_name,
                "API": [
                    self.gbif_species_suggest_stub.format(scientific_name)
                ],
                "GBIF Species Suggestions": len(gbif_spp_search_results)
            },
            "GBIF Species Record": gbif_spp_search_results[0]
        }

        if "nubKey" in species_summary["GBIF Species Record"].keys():
            species_summary["Processing Metadata"]["API"].append(
                self.gbif_spp_occ_summary_api.format(
                    "taxon-Key",
                    species_summary["GBIF Species Record"]["nubKey"]
                )
            )
        else:
            species_summary["Processing Metadata"]["API"].append(
                self.gbif_spp_occ_summary_api.format(
                    "scientificName",
                    scientific_name
                )
            )

        gbif_occ_results = requests.get(
            species_summary["Processing Metadata"]["API"][-1]
        ).json()

        for key in ["endOfRecords", "limit", "offset", "results"]:
            del gbif_occ_results[key]

        species_summary["Occurrence Summary"] = gbif_occ_results

        return species_summary

