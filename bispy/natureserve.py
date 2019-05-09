class Natureserve:
    def __init__(self):
        self.description = "Set of functions for working with the NatureServe APIs"
        self.ns_api_base = "https://services.natureserve.org/idd/rest/v1"
        self.us_name_search_api = "nationalSpecies/summary/nameSearch?nationCode=US"

    def search(self, scientificname):
        import requests
        import xmltodict
        from datetime import datetime

        result = dict()
        result["Processing Metadata"] = dict()
        result["Processing Metadata"]["Date Processed"] = datetime.utcnow().isoformat()
        result["Processing Metadata"]["Summary Result"] = "Not Matched"
        result["Processing Metadata"]["Search URL"] = \
            f"{self.ns_api_base}/{self.us_name_search_api}&name={scientificname}"

        ns_api_result = requests.get(result["Processing Metadata"]["Search URL"])

        if ns_api_result.status_code != 200:
            return None
        else:
            ns_dict = xmltodict.parse(ns_api_result.text, dict_constructor=dict)

            if "species" not in ns_dict["speciesList"].keys():
                return None
            else:
                if isinstance(ns_dict["speciesList"]["species"], list):
                    ns_species = next(
                        (
                            r for r in ns_dict["speciesList"]["species"]
                            if r["nationalScientificName"] == scientificname
                         ),
                        None
                    )
                    if ns_species is not None:
                        result["NatureServe Species"] = ns_species
                else:
                    result["NatureServe Species"] = ns_dict["speciesList"]["species"]

        return result

