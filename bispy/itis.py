from datetime import datetime
import requests
from . import bis
import re

bis_utils = bis.Utils()

class Itis:
    def __init__(self):
        self.description = "Set of functions for interacting with ITIS"

    def package_itis_json(self, itisDoc):
        itis_data = {}

        if type(itisDoc) is not int:
            # Get rid of parts of the ITIS doc that we don't want/need to cache
            primaryKeysToPop = ["_version_", "credibilityRating", "expert", "geographicDivision", "hierarchicalSort",
                                "hierarchyTSN", "jurisdiction", "publication", "rankID", "otherSource", "taxonAuthor",
                                "comment"]

            for key in primaryKeysToPop:
                itisDoc.pop(key, None)

            # Convert date properties to common property names
            itisDoc["date_created"] = itisDoc.pop("createDate")
            itisDoc["date_modified"] = itisDoc.pop("updateDate")

            # Make a clean structure of the taxonomic hierarchy
            # Make a clean structure of the taxonomic hierarchy
            itisDoc["biological_taxonomy"] = []
            for rank in itisDoc['hierarchySoFarWRanks'][0][itisDoc['hierarchySoFarWRanks'][0].find(':$') + 2:-1].split(
                    "$"):
                thisRankName = {}
                thisRankName["rank"] = rank.split(":")[0]
                thisRankName["name"] = rank.split(":")[1]
                itisDoc["biological_taxonomy"].append(thisRankName)
            itisDoc.pop("hierarchySoFarWRanks", None)

            # Make a clean, usable list of the hierarchy so far for display or listing
            itisDoc["hierarchy"] = itisDoc["hierarchySoFar"][0].split(":")[1][1:-1].split("$")
            itisDoc.pop("hierarchySoFar", None)

            # Make a clean structure of common names
            if "vernacular" in itisDoc:
                itisDoc["commonnames"] = []
                for commonName in itisDoc['vernacular']:
                    thisCommonName = {}
                    thisCommonName["name"] = commonName.split('$')[1]
                    thisCommonName["language"] = commonName.split('$')[2]
                    itisDoc["commonnames"].append(thisCommonName)
                itisDoc.pop("vernacular", None)

            # Add the new ITIS doc to the ITIS data structure and return
            itis_data.update(itisDoc)

        return itis_data

    def get_itis_search_url(self, searchstr, fuzzy=False, validAccepted=True):
        fuzzyLevel = "~0.8"

        api_stub = "https://services.itis.gov/?wt=json&rows=10&q="
        search_term = "nameWOInd"
        searchstr = str(searchstr)

        if searchstr.isdigit():
            search_term = "tsn"
        else:
            searchstr = '\%20'.join(re.split(' +', searchstr))
            if searchstr.find("var.") > 0 or searchstr.find("ssp.") > 0 or searchstr.find(" x ") > 0:
                search_term = "nameWInd"

        api = f"{api_stub}{search_term}:{searchstr}"

        if fuzzy:
            api = f"{api}{fuzzyLevel}"

        if validAccepted:
            api = f"{api}%20AND%20(usage:accepted%20OR%20usage:valid)"

        return api

    def search(self, scientificname):
        # Set up itis_result structure to return and prep the processingMetadata, set a default for Summary Result to Not Matched
        itis_result =  bis_utils.processing_metadata()
        itis_result["processing_metadata"]["status_message"] = "Not Matched"
        itis_result["processing_metadata"]["details"] = []

        # Set up the primary search method for an exact match on scientific name
        url_exactMatch = self.get_itis_search_url(scientificname, False, False)

        # We have to try the main search queries because the ITIS service does not return an elegant error
        try:
            r_exactMatch = requests.get(url_exactMatch).json()
        except:
            itis_result["processing_metadata"]["details"].append({"Hard Fail Query": url_exactMatch})
            itis_result["processing_metadata"]["status_message"] = "Hard Fail Query"
            itis_result["processing_metadata"]["status"] = "error"
            return itis_result

        if r_exactMatch["response"]["numFound"] == 0:

            itis_result["processing_metadata"]["details"].append({"Exact Match Fail": url_exactMatch})

            # if we didn't get anything with an exact name match, run the sequence using fuzziness level
            url_fuzzyMatch = self.get_itis_search_url(scientificname, True, False)

            try:
                r_fuzzyMatch = requests.get(url_fuzzyMatch).json()
            except:
                itis_result["processing_metadata"]["details"].append({"Hard Fail Query": url_fuzzyMatch})
                itis_result["processing_metadata"]["status_message"] = "Hard Fail Query"
                itis_result["processing_metadata"]["status"] = "error"
                return itis_result

            if r_fuzzyMatch["response"]["numFound"] == 0:
                # If we still get no results then provide the specific detailed result
                itis_result["processing_metadata"]["details"].append({"Fuzzy Match Fail": url_fuzzyMatch})
                return itis_result

            elif r_fuzzyMatch["response"]["numFound"] > 0:
                # If we got one or more results with a fuzzy match, we will just use the first result
                itis_result["itis_data"] = []

                # We need to check to see if the discovered ITIS record is accepted for use. If not, we need to follow the accepted TSN in that document
                if r_fuzzyMatch["response"]["docs"][0]["usage"] in ["invalid", "not accepted"]:
                    url_tsnSearch = self.get_itis_search_url(r_fuzzyMatch["response"]["docs"][0]["acceptedTSN"][0], False,
                                                     False)
                    r_tsnSearch = requests.get(url_tsnSearch).json()
                    itis_result["itis_data"].append(self.package_itis_json(r_tsnSearch["response"]["docs"][0]))
                    itis_result["processing_metadata"]["status"] = "success"
                    itis_result["processing_metadata"]["status_message"] = "Followed Accepted TSN"
                    itis_result["processing_metadata"]["details"].append({"TSN Search": url_tsnSearch})
                else:
                    itis_result["processing_metadata"]["status"] = "success"
                    itis_result["processing_metadata"]["status_message"] = "Fuzzy Match"

                # Whether or not we needed to follow an accepted TSN, we will also include the ITIS record that was the point of discovery
                itis_result["processing_metadata"]["details"].append({"Fuzzy Match": url_fuzzyMatch})
                itis_result["itis_data"].append(self.package_itis_json(r_fuzzyMatch["response"]["docs"][0]))

        elif r_exactMatch["response"]["numFound"] == 1:
            # If we found only one record with the exact match query, we treat that as a useful point of discovery

            itis_result["itis_data"] = []

            # We need to check to see if the discovered ITIS record is accepted for use. If not, we need to follow the accepted TSN in that document
            if r_exactMatch["response"]["docs"][0]["usage"] in ["invalid", "not accepted"]:
                url_tsnSearch = self.get_itis_search_url(r_exactMatch["response"]["docs"][0]["acceptedTSN"][0], False, False)
                r_tsnSearch = requests.get(url_tsnSearch).json()
                itis_result["itis_data"].append(self.package_itis_json(r_tsnSearch["response"]["docs"][0]))
                itis_result["processing_metadata"]["status"] = "success"
                itis_result["processing_metadata"]["status_message"] = "Followed Accepted TSN"
                itis_result["processing_metadata"]["details"].append({"TSN Search": url_tsnSearch})
            else:
                itis_result["processing_metadata"]["status"] = "success"
                itis_result["processing_metadata"]["status_message"] = "Exact Match"

            # Whether or not we needed to follow an accepted TSN, we will also include the ITIS record that was the point of discovery
            itis_result["processing_metadata"]["details"].append({"Exact Match": url_exactMatch})
            itis_result["itis_data"].append(self.package_itis_json(r_exactMatch["response"]["docs"][0]))

        elif r_exactMatch["response"]["numFound"] > 1:
            # If we find more than one document with an exact match search, we can make a few more decisions based on what's in the data before we need to punt the rest to human supervision

            itis_result["processing_metadata"]["details"].append({"Multi Match": url_exactMatch})

            # First we assemble the set of acceptedTSNs for the discovered records so that we can determine if there is only a single accepted record to follow
            # This step might need review by the ITIS team, but it seems reasonable for the records we have looked at so far
            acceptedTSNs = []
            for itisDoc in r_exactMatch["response"]["docs"]:
                if "acceptedTSN" in itisDoc.keys() and itisDoc["acceptedTSN"][0] not in acceptedTSNs:
                    acceptedTSNs.append(itisDoc["acceptedTSN"][0])

            if len(acceptedTSNs) == 1:
                # Multiple exact matches were returned, but only one of them has an accepted TSN to follow
                itis_result["itis_data"] = []
                url_tsnSearch = self.get_itis_search_url(acceptedTSNs[0], False, True)
                r_tsnSearch = requests.get(url_tsnSearch).json()
                itis_result["itis_data"].append(self.package_itis_json(r_tsnSearch["response"]["docs"][0]))
                itis_result["processing_metadata"]["status"] = "success"
                itis_result["processing_metadata"]["status_message"] = "Followed Accepted TSN"
                itis_result["processing_metadata"]["details"].append({"TSN Search": url_tsnSearch})

            else:
                # If there are multiple acceptedTSN values for multiple returned exact match records, we don't yet know what to do with these.
                # Some combination of factors in the data or a deeper level search from the source may come up with a way to make the algorithm more sophisticated.
                itis_result["processing_metadata"]["status"] = "failure"
                itis_result["processing_metadata"]["status_message"] = "Indeterminate Results"

        return itis_result
