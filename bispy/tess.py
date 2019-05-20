import requests
import xmltodict
import bis

class Tess:
    def __init__(self):
        self.description = 'Set of functions for working with the USFWS Threatened and Endangered Species System'
        self.tess_api_base = "https://ecos.fws.gov/ecp0/TessQuery?request=query&xquery=/SPECIES_DETAIL"
        self.response_result = bis.response_result()

    def search(self, scientificname):

        tess_result = self.response_result
        tess_result["Processing Metadata"]["Summary Result"] = "Not Matched"
        tess_result["Processing Metadata"]["Search URL"] = f'{self.tess_api_base}[SCINAME="{scientificname}"]'

        # Query the TESS XQuery service
        tess_response = requests.get(tess_result["Processing Metadata"]["Search URL"])

        if tess_response.status_code != 200:
            return tess_result

        # Build an unordered dict from the TESS XML response (we don't care about ordering for our purposes here)
        tessDict = xmltodict.parse(tess_response.text, dict_constructor=dict)

        if "results" not in tessDict.keys() or tessDict["results"] is None:
            return tess_result

        tess_result["TESS Species"] = tessDict["results"]

        return tess_result

