import requests
from datetime import datetime


class Sciencebase:
    def __init__(self):
        self.sb_catalog_items_api = "https://www.sciencebase.gov/catalog/items"

    def collection_items(self, collectionid, fields="id"):
        '''
        Loops through specified ScienceBase collection to return all items in a list with a set of fields. This
        function handles the issue of looping through the ScienceBase pagination when you need to get more items than
        the maximum that can be returned.

        :param collectionid: ScienceBase parent item ID
        :param fields: List of ScienceBase Item fields to return
        :return: List of the ScienceBase Items within the GAP species
        '''
        nextlink = f"{self.sb_catalog_items_api}?max=100&parentId={collectionid}&format=json&fields={fields}"

        item_list = list()

        while nextlink is not None:
            r = requests.get(nextlink).json()
            item_list.extend(r["items"])
            if "nextlink" in r.keys():
                nextlink = r["nextlink"]["url"]
            else:
                nextlink = None

        return item_list


def response_result():
    response_result = dict()
    response_result["Processing Metadata"] = dict()
    response_result["Processing Metadata"]["Status"] = "Error"
    response_result["Processing Metadata"]["Message"] = "No Message Recorded"
    response_result["Processing Metadata"]["Date Processed"] = datetime.utcnow().isoformat()
    response_result["Processing Metadata"]["Number Documents"] = 0
    response_result["Processing Metadata"]["Search URL"] = ""
    return response_result
