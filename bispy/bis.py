import requests


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

