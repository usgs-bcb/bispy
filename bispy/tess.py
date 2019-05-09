class Tess:
    def __init__(self):
        self.description = 'Set of functions for working with the USFWS Threatened and Endangered Species System'
        self.tess_api_base = "https://ecos.fws.gov/ecp0/TessQuery?request=query&xquery=/SPECIES_DETAIL"

    def search(self, scientificname):
        import requests
        import xmltodict
        from datetime import datetime

        tessResult = dict()
        tessResult["Processing Metadata"] = dict()
        tessResult["Processing Metadata"]["Date Processed"] = datetime.utcnow().isoformat()
        tessResult["Processing Metadata"]["Summary Result"] = "Not Matched"
        tessResult["Processing Metadata"]["Search URL"] = f'{self.tess_api_base}[SCINAME="{scientificname}"]'

        # Query the TESS XQuery service
        tess_response = requests.get(tessResult["Processing Metadata"]["Search URL"])

        if tess_response.status_code != 200:
            return tessResult

        # Build an unordered dict from the TESS XML response (we don't care about ordering for our purposes here)
        tessDict = xmltodict.parse(tess_response.text, dict_constructor=dict)

        if "results" not in tessDict.keys() or tessDict["results"] is None:
            return tessResult

        tessResult["TESS Species"] = tessDict["results"]

        return tessResult

