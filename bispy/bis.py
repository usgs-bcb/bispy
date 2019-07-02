import requests
from datetime import datetime
from collections import Counter


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


class Utils:
    def __init__(self):
        self.data = {}
  
    def processing_metadata(self, default_status="Error"):
        packaged_stub = {
            "Processing Metadata": {
                "Status": default_status,
                "Date Processed": datetime.utcnow().isoformat()
            }
        }
        return packaged_stub


class AttributeValueCount:
    def __init__(self, iterable, *, missing=None):
        self._missing = missing
        self.length = 0
        self._counts = {}
        self.update(iterable)

    def update(self, iterable):
        categories = set(self._counts)
        for length, element in enumerate(iterable, self.length):
            categories.update(element)
            for category in categories:
                try:
                    counter = self._counts[category]
                except KeyError:
                    self._counts[category] = counter = Counter({self._missing: length})
                counter[element.get(category, self._missing)] += 1
        self.length = length + 1

    def add(self, element):
        self.update([element])

    def __getitem__(self, key):
        return self._counts[key]

    def summary(self, key=None):
        if key is None:
            return '\n'.join(self.summary(key) for key in self._counts)

        return '-- {} --\n{}'.format(key, '\n'.join(
                '\t {}: {}'.format(value, count)
                for value, count in self._counts[key].items()
        ))
