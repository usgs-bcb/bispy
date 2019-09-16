import requests
from . import bis

bis_utils = bis.Utils()


class Gbif:
    def __init__(self):
        self.gbif_spp_occ_summary_api = "https://api.gbif.org/v1/occurrence/search?country=US&limit=0&facet=institutionCode&facet=year&facet=basisOfRecord&{}={}"
        self.gbif_species_suggest_stub = "https://api.gbif.org/v1/species/suggest?q={}"
        self.gbif_species_api_root = "http://api.gbif.org/v1/species/"

    def build_gbif_taxonomy(self, gbif_species):
        taxonomy = list()
        for k, v in gbif_species.items():
            if k.find("Key") > 0:
                key_to_use = k.replace('Key', '')
                if key_to_use not in ["nub", "parent"]:
                    taxonomy.append({
                        "rank": key_to_use,
                        "name": gbif_species[key_to_use]
                    })

        return taxonomy

    def summarize_us_species(self, scientificname, name_source=None):
        result = bis_utils.processing_metadata()
        result["processing_metadata"]["status"] = "failure"
        result["processing_metadata"]["status_message"] = "Not Matched"
        result["processing_metadata"]["api"] = [
            self.gbif_species_suggest_stub.format(scientificname)
        ]

        result["parameters"] = {
            "Scientific Name": scientificname
        }

        if name_source is not None:
            result["parameters"]["Name Source"] = name_source

        gbif_spp_search_results = requests.get(self.gbif_species_suggest_stub.format(scientificname)).json()

        if len(gbif_spp_search_results) == 0:
            result["processing_metadata"]["status"] = "failure"
            return result

        result["data"] = {
            "key": gbif_spp_search_results[0]["key"],
            "resolvable_identifier": f"{self.gbif_species_api_root}{gbif_spp_search_results[0]['key']}",
            "biological_taxonomy": self.build_gbif_taxonomy(gbif_spp_search_results[0]),
            "Scientific Name": gbif_spp_search_results[0]["canonicalName"],
            "name_with_source": gbif_spp_search_results[0]["scientificName"],
            "rank": gbif_spp_search_results[0]["rank"],
            "TaxonomicStatus": gbif_spp_search_results[0]["status"],
            "synonym": gbif_spp_search_results[0]["synonym"]
        }

        if "nubKey" in result["gbif_species"].keys():
            result["processing_metadata"]["api"].append(
                self.gbif_spp_occ_summary_api.format(
                    "taxon-Key",
                    result["data"]["nubKey"]
                )
            )
        else:
            result["processing_metadata"]["api"].append(
                self.gbif_spp_occ_summary_api.format(
                    "scientificName",
                    scientificname
                )
            )

        gbif_occ_results = requests.get(
            result["processing_metadata"]["api"][-1]
        ).json()

        for key in ["endOfRecords", "limit", "offset", "results"]:
            del gbif_occ_results[key]

        result["processing_metadata"]["status_message"] = "Matched"
        result["processing_metadata"]["status"] = "success"
        result["data"]["Occurrence Summary"] = gbif_occ_results

        return result

