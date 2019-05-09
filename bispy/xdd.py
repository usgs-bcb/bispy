from datetime import datetime
import requests

class Xdd:
    def __init__(self):
        self.xdd_api_base = "https://geodeepdive.org/api"

    def snippets(self, term):
        api_route = f"{self.xdd_api_base}/snippets?full_results"

        xdd_result = dict()
        xdd_result["Processing Metadata"] = dict()
        xdd_result["Processing Metadata"]["Date Processed"] = datetime.utcnow().isoformat()
        xdd_result["Processing Metadata"]["Number Documents"] = 0
        xdd_result["Processing Metadata"]["Search URL"] = f"{api_route}&term={term}"

        xdd_response = requests.get(xdd_result["Processing Metadata"]["Search URL"])
        if xdd_response.status_code != 200 or "success" not in xdd_response.json():
            return xdd_result

        xdd_resultset = xdd_response.json()
        xdd_result["Processing Metadata"]["Number Documents"] = int(xdd_resultset["success"]["hits"])
        if xdd_result["Processing Metadata"]["Number Documents"] == 0:
            return xdd_result
        else:
            xdd_result["xDD Documents"] = xdd_resultset["success"]["data"]

            search_url = xdd_resultset["success"]["next_page"]
            while len(search_url) > 0:
                next_resultset = requests.get(search_url).json()
                xdd_result["xDD Documents"] += next_resultset["success"]["data"]
                search_url = next_resultset["success"]["next_page"]

            return xdd_result