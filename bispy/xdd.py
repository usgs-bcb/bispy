from datetime import datetime
import requests
import bis

class Xdd:
    def __init__(self, search_term=''):
        self.xdd_api_base = "https://geodeepdive.org/api"
        self.response_result = bis.response_result()
        self.search_term = search_term
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

        xdd_result = self.response_result
        self.search_term = search_term
        self.url = f"{api_route}&term={search_term}"
        xdd_result["Processing Metadata"]["Search URL"] = self.url

        xdd_response = requests.get(xdd_result["Processing Metadata"]["Search URL"])
        if xdd_response.status_code != 200:
            xdd_result["Processing Metadata"]["Summary Result"] = f"The following status code was returned: {xdd_response.status_code}"
            return resonse_result
        
        elif "success" not in xdd_response.json():
            xdd_result["Processing Metadata"]["Summary Result"] = "No data returned. Verify request is valid."
            return xdd_result
        
        xdd_resultset = xdd_response.json()

        xdd_result["Processing Metadata"]["Number Documents"] = int(xdd_resultset["success"]["hits"])
        #Handle no returned data
        if xdd_result["Processing Metadata"]["Number Documents"] == 0:
            xdd_result["Processing Metadata"]["Summary Result"] = "No data returned."
            return xdd_result
        #Handle paging through results
        elif xdd_resultset["success"]["next_page"]:
            xdd_result["Processing Metadata"]["Status"] = "Success"
            xdd_result["Data"] = xdd_resultset["success"]["data"]
            search_url = xdd_resultset["success"]["next_page"]
            while len(search_url) > 0:
                xdd_next_response = requests.get(search_url)
                if xdd_next_response.status_code != 200:
                    #Might want to try resending request before documenting error and moving on    
                    #This clears Data to ensure we don't use a partial return of data here or leave what was successful?
                    xdd_result.pop("Data", None)
                    xdd_result["Processing Metadata"]["Status"] = "Error"
                    xdd_result["Processing Metadata"]["Summary Result"] = f"Incomplete results. While paging results the following status code was returned: {xdd_response.status_code}"
                    return xdd_result
                else:
                    xdd_next_resultset = xdd_next_response.json()
                    xdd_result["Data"] += xdd_next_resultset["success"]["data"]
                    search_url = xdd_next_resultset["success"]["next_page"]
                    return xdd_result
            
        #Handle if nextpage is not available
        else:
            xdd_result["Processing Metadata"]["Status"] = "Success"
            xdd_result["Data"] = xdd_resultset["success"]["data"]
            return xdd_result