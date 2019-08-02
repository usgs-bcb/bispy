from . import bis
import requests

bis_utils = bis.Utils()

class Xdd:
    def __init__(self, search_term=''):
        self.xdd_api_base = "https://geodeepdive.org/api"
        self.search_term = search_term
        self.snippets_property_mapping = {
            "title": "document_title",
            "URL": "document_link"
        }
        self.url = ''

    #Supporting information to reconstruct an object
    def __repr__(self):
        return f"Xdd({self.xdd_api_base},{self.search_term})"

    #Allows for a meaningful print of the object
    def __str__(self):
        return f"term: {self.search_term}\n\
url: {self.url}"

    def snippets(self, search_term):
        api_route = f"{self.xdd_api_base}/snippets?full_results&clean"

        xdd_result = bis_utils.processing_metadata()
        self.search_term = search_term
        self.url = f"{api_route}&term={search_term}"
        xdd_result["processing_metadata"]["api"] = self.url
        xdd_result["parameters"] = {
            "Search Term": search_term
        }

        xdd_response = requests.get(xdd_result["processing_metadata"]["api"])
        if xdd_response.status_code != 200:
            xdd_result["processing_metadata"]["status"] = "error"
            xdd_result["processing_metadata"]["status_message"] = f"The following status code was returned: {xdd_response.status_code}"
            return xdd_result
        
        elif "success" not in xdd_response.json():
            xdd_result["processing_metadata"]["status"] = "failure"
            xdd_result["processing_metadata"]["status_message"] = "No data returned. Verify request is valid."
            return xdd_result
        
        xdd_resultset = xdd_response.json()

        #Handle no returned data
        if int(xdd_resultset["success"]["hits"]) == 0:
            xdd_result["processing_metadata"]["status"] = "failure"
            xdd_result["processing_metadata"]["status_message"] = "No data returned."
            return xdd_result
        #Handle paging through results
        elif xdd_resultset["success"]["next_page"]:
            xdd_result["processing_metadata"]["status"] = "success"
            xdd_result["xdd_documents"] = xdd_resultset["success"]["data"]
            search_url = xdd_resultset["success"]["next_page"]
            while len(search_url) > 0:
                xdd_next_response = requests.get(search_url)
                if xdd_next_response.status_code != 200:
                    #Might want to try resending request before documenting error and moving on    
                    #This clears Data to ensure we don't use a partial return of data here or leave what was successful?
                    xdd_result.pop("Data", None)
                    xdd_result["processing_metadata"]["status"] = "error"
                    xdd_result["processing_metadata"]["status_message"] = \
                        f"Incomplete results. While paging results the following status code was returned: " \
                        f"{xdd_response.status_code}"
                    return xdd_result
                else:
                    xdd_next_resultset = xdd_next_response.json()
                    xdd_result["xdd_documents"] += xdd_next_resultset["success"]["data"]
                    search_url = xdd_next_resultset["success"]["next_page"]

        #Handle if nextpage is not available
        else:
            xdd_result["processing_metadata"]["status"] = "success"
            xdd_result["xdd_documents"] = xdd_resultset["success"]["data"]

        if "xdd_documents" in xdd_result.keys():
            for record in xdd_result["xdd_documents"]:
                for k, v in self.snippets_property_mapping.items():
                    record[v] = record.pop(k)

        return xdd_result
