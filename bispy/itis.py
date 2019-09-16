import requests
from . import bis
import re

bis_utils = bis.Utils()

class Itis:
    def __init__(self):
        self.description = "Set of functions for interacting with ITIS Solr API and repackaging results for usability"

    def package_itis_json(self, itisDoc):
        itis_data = {}

        if type(itisDoc) is not int:
            # Get rid of parts of the ITIS doc that we don't want/need to cache
            discard_keys = ["hierarchicalSort", "hierarchyTSN"]

            for key in discard_keys:
                itisDoc.pop(key, None)

            # Convert date properties to common property names
            itisDoc["date_created"] = itisDoc.pop("createDate")
            itisDoc["date_modified"] = itisDoc.pop("updateDate")

            # Parse geographicDivision and jurisdiction into a more useful format
            list_geographicDivision = itisDoc.pop("geographicDivision", None)
            list_jurisdiction = itisDoc.pop("jurisdiction", None)

            if list_geographicDivision is not None:
                itisDoc["geographicDivision"] = list()
                for geodiv in list_geographicDivision:
                    itisDoc["geographicDivision"].append({
                        "geographic_value": geodiv.split("$")[1],
                        "update_date": geodiv.split("$")[2]
                    })

            if list_jurisdiction is not None:
                itisDoc["jurisdiction"] = list()
                for jur in list_jurisdiction:
                    itisDoc["jurisdiction"].append({
                        "jurisdiction_value": jur.split("$")[1],
                        "origin": jur.split("$")[2],
                        "update_date": jur.split("$")[3]
                    })

            # Parse expert(s) into a more useful format
            list_expert = itisDoc.pop("expert", None)

            if list_expert is not None:
                itisDoc["expert"] = list()
                for exp in list_expert:
                    itisDoc["expert"].append({
                        "reference_type": exp.split("$")[1],
                        "expert_id": exp.split("$")[2],
                        "expert_name": exp.split("$")[3],
                        "expert_comment": exp.split("$")[4],
                        "create_date": exp.split("$")[5],
                        "update_date": exp.split("$")[6]
                    })

            # Parse publications(s) into a more useful format
            list_publication = itisDoc.pop("publication", None)

            if list_publication is not None:
                itisDoc["publication"] = list()
                for pub in list_publication:
                    pub_doc = {
                        "reference_type": pub.split("$")[1],
                        "reference_id": pub.split("$")[2],
                        "author": pub.split("$")[3],
                        "title": pub.split("$")[5],
                    }
                    for index, var in enumerate(pub.split("$")[6:]):
                        if len(var) > 0:
                            pub_doc[f"other_variable_{index}"] = var
                    itisDoc["publication"].append(pub_doc)

            # Parse otherSource into a more useful format
            list_other_source = itisDoc.pop("otherSource", None)

            if list_other_source is not None:
                itisDoc["otherSource"] = list()
                for src in list_other_source:
                    try:
                        itisDoc["otherSource"].append({
                            "reference_type": src.split("$")[1],
                            "source_id": src.split("$")[2],
                            "source_type": src.split("$")[3],
                            "source_name": src.split("$")[4],
                            "version": src.split("$")[5],
                            "acquisition_date": src.split("$")[6],
                            "source_comment": src.split("$")[7],
                            "create_date": src.split("$")[8],
                            "update_date": src.split("$")[9]
                        })
                    except:
                        itisDoc["otherSource"].append({
                            "raw_text": src
                        })

            # Parse comment into a more useful format
            list_comment = itisDoc.pop("comment", None)

            if list_comment is not None:
                itisDoc["comment"] = list()
                for comment in list_comment:
                    try:
                        itisDoc["comment"].append({
                            "comment_id": comment.split("$")[1],
                            "commentator": comment.split("$")[2],
                            "comment_text": comment.split("$")[3],
                            "create_date": comment.split("$")[4],
                            "update_date": comment.split("$")[5]
                        })
                    except:
                        itisDoc["comment"].append({
                            "raw_text": comment
                        })

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

    def search(self, name_or_tsn, name_source=None):
        # Set up itis_result structure to return and prep the processingMetadata, set a default for Summary Result
        # to Not Matched
        itis_result = bis_utils.processing_metadata()
        itis_result["processing_metadata"]["status_message"] = "Not Matched"
        itis_result["processing_metadata"]["details"] = []

        if name_or_tsn.isdigit():
            search_param = "TSN"
        else:
            search_param = "Scientific Name"

        itis_result["parameters"] = {
            search_param: name_or_tsn
        }

        if name_source is not None:
            itis_result["parameters"]["Name Source"] = name_source

        # Set up the primary search method for an exact match on scientific name
        url_exactMatch = self.get_itis_search_url(name_or_tsn, False, False)

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
            url_fuzzyMatch = self.get_itis_search_url(name_or_tsn, True, False)

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
                itis_result["data"] = []

                # We need to check to see if the discovered ITIS record is accepted for use. If not, we need to follow
                # the accepted TSN in that document
                if r_fuzzyMatch["response"]["docs"][0]["usage"] in ["invalid", "not accepted"]:
                    url_tsnSearch = self.get_itis_search_url(
                        r_fuzzyMatch["response"]["docs"][0]["acceptedTSN"][0], False, False
                    )
                    r_tsnSearch = requests.get(url_tsnSearch).json()
                    itis_result["data"].append(self.package_itis_json(r_tsnSearch["response"]["docs"][0]))
                    itis_result["processing_metadata"]["status"] = "success"
                    itis_result["processing_metadata"]["status_message"] = "Followed Accepted TSN"
                    itis_result["processing_metadata"]["details"].append({"TSN Search": url_tsnSearch})
                else:
                    itis_result["processing_metadata"]["status"] = "success"
                    itis_result["processing_metadata"]["status_message"] = "Fuzzy Match"

                # Whether or not we needed to follow an accepted TSN, we will also include the ITIS record that was
                # the point of discovery
                itis_result["processing_metadata"]["details"].append({"Fuzzy Match": url_fuzzyMatch})
                itis_result["data"].append(self.package_itis_json(r_fuzzyMatch["response"]["docs"][0]))

        elif r_exactMatch["response"]["numFound"] == 1:
            # If we found only one record with the exact match query, we treat that as a useful point of discovery

            itis_result["data"] = list()

            # We need to check to see if the discovered ITIS record is accepted for use. If not, we need to follow
            # the accepted TSN in that document
            if r_exactMatch["response"]["docs"][0]["usage"] in ["invalid", "not accepted"]:
                url_tsnSearch = self.get_itis_search_url(
                    r_exactMatch["response"]["docs"][0]["acceptedTSN"][0], False, False
                )
                r_tsnSearch = requests.get(url_tsnSearch).json()
                itis_result["data"].append(self.package_itis_json(r_tsnSearch["response"]["docs"][0]))
                itis_result["processing_metadata"]["status"] = "success"
                itis_result["processing_metadata"]["status_message"] = "Followed Accepted TSN"
                itis_result["processing_metadata"]["details"].append({"TSN Search": url_tsnSearch})
            else:
                itis_result["processing_metadata"]["status"] = "success"
                itis_result["processing_metadata"]["status_message"] = "Exact Match"

            # Whether or not we needed to follow an accepted TSN, we will also include the ITIS record that was the
            # point of discovery
            itis_result["processing_metadata"]["details"].append({"Exact Match": url_exactMatch})
            itis_result["data"].append(self.package_itis_json(r_exactMatch["response"]["docs"][0]))

        elif r_exactMatch["response"]["numFound"] > 1:
            # If we find more than one document with an exact match search, we can make a few more decisions based
            # on what's in the data before we need to punt the rest to human supervision

            itis_result["processing_metadata"]["details"].append({"Multi Match": url_exactMatch})

            # First we assemble the set of acceptedTSNs for the discovered records so that we can determine if there
            # is only a single accepted record to follow. This step might need review by the ITIS team, but it seems
            # reasonable for the records we have looked at so far
            acceptedTSNs = []
            for itisDoc in r_exactMatch["response"]["docs"]:
                if "acceptedTSN" in itisDoc.keys() and itisDoc["acceptedTSN"][0] not in acceptedTSNs:
                    acceptedTSNs.append(itisDoc["acceptedTSN"][0])

            if len(acceptedTSNs) == 1:
                # Multiple exact matches were returned, but only one of them has an accepted TSN to follow
                itis_result["data"] = list()
                url_tsnSearch = self.get_itis_search_url(acceptedTSNs[0], False, True)
                r_tsnSearch = requests.get(url_tsnSearch).json()
                itis_result["data"].append(self.package_itis_json(r_tsnSearch["response"]["docs"][0]))
                itis_result["processing_metadata"]["status"] = "success"
                itis_result["processing_metadata"]["status_message"] = "Followed Accepted TSN"
                itis_result["processing_metadata"]["details"].append({"TSN Search": url_tsnSearch})

            else:
                # If there are multiple acceptedTSN values for multiple returned exact match records, we don't yet
                # know what to do with these. Some combination of factors in the data or a deeper level search from
                # the source may come up with a way to make the algorithm more sophisticated.
                itis_result["processing_metadata"]["status"] = "failure"
                itis_result["processing_metadata"]["status_message"] = "Indeterminate Results"

        return itis_result
