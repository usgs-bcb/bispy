from datetime import datetime
import requests

class Xdd:
    def __init__(self):
        self.xdd_api_base = "https://geodeepdive.org/api"

    def snippets(self, term):
        api_route = f"{self.xdd_api_base}/snippets?full_results&clean"

        response_result = Xdd.response_result()
        response_result["Processing Metadata"]["Search URL"] = f"{api_route}&term={term}"

        xdd_response = requests.get(response_result["Processing Metadata"]["Search URL"])
        if xdd_response.status_code != 200:
            response_result["Message"] = f"The following status code was returned: {xdd_response.status_code}"
            return resonse_result
        
        elif "success" not in xdd_response.json():
            response_result["Message"] = "No data returned. Verify request is valid."
            return response_result
        
        xdd_resultset = xdd_response.json()

        response_result["Processing Metadata"]["Number Documents"] = int(xdd_resultset["success"]["hits"])
        #Handle no returned data
        if response_result["Processing Metadata"]["Number Documents"] == 0:
            response_result["Message"] = "No data returned."
            return response_result
        #Handle paging through results
        elif xdd_resultset["success"]["next_page"]:
            response_result["Status"] = "Success"
            response_result["Data"] = xdd_resultset["success"]["data"]
            search_url = xdd_resultset["success"]["next_page"]
            while len(search_url) > 0:
                xdd_next_response = requests.get(search_url)
                if xdd_next_response.status_code != 200:
                    #Might want to try resending request before documenting error and moving on    
                    #This clears Data to ensure we don't use a partial return of data here or leave what was successful?
                    response_result.pop("Data", None)
                    response_result["Status"] = "Error"
                    response_result["Message"] = f"Incomplete results. While paging results the following status code was returned: {xdd_response.status_code}"
                    return response_result
                else:
                    xdd_next_resultset = xdd_next_response.json()
                    response_result["Data"] += xdd_next_resultset["success"]["data"]
                    search_url = xdd_next_resultset["success"]["next_page"]
                    return response_result
            
        #Handle if nextpage is not available
        else:
            response_result["Status"] = "Success"
            response_result["Data"] = xdd_resultset["success"]["data"]
            return response_result
        
    def response_result():
        response_result = dict()
        response_result["Status"] = "Error"
        response_result["Processing Metadata"] = dict()
        response_result["Processing Metadata"]["Date Processed"] = datetime.utcnow().isoformat()
        response_result["Processing Metadata"]["Number Documents"] = 0
        return response_result