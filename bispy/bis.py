import requests
from datetime import datetime
from collections import Counter
import random
import os
import json
from genson import SchemaBuilder


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
  
    def processing_metadata(self, default_status="error"):
        packaged_stub = {
            "processing_metadata": {
                "status": default_status,
                "date_processed": datetime.utcnow().isoformat()
            }
        }
        return packaged_stub

    def doc_cache(self, cache_path, cache_data=None, return_sample=True):
        '''
        Caches a list of dictionaries as a JSON document array to a specified relative path and returns a sample.

        :param cache_path: relative file path to write to; will overwrite if it exists
        :param cache_data: list of dictionaries to cache as JSON document array
        :param return_sample: return a random sample for verification
        :return:
        '''
        if cache_data is not None:
            if not isinstance(cache_data, list):
                return "Error: cache_data needs to be a list of dictionaries"

            if len(cache_data) == 0:
                return "Error: cache_data needs to be a list with at least one dictionary"

            if not isinstance(cache_data[0], dict):
                return "Error: cache_data needs to be a list of dictionaries"

            try:
                with open(cache_path, "w") as f:
                    f.write(json.dumps(cache_data))
            except Exception as e:
                return f"Error: {e}"

        if not return_sample:
            return "Success"
        else:
            if not os.path.exists(cache_path):
                return "Error: file does not exist"

            try:
                with open(cache_path, "r") as f:
                    the_cache = json.loads(f.read())
            except Exception as e:
                return f"Error: {e}"

            if not isinstance(the_cache, list):
                return "Error: file does not contain an array"

            if not isinstance(the_cache[0], dict):
                return "Error: file does not contain an array of JSON objects (documents)"

            doc_number = random.randint(0, len(the_cache) - 1)
            return {
                "Doc Cache File": cache_path,
                "Number of Documents in Cache": len(the_cache),
                f"Document Number {doc_number}": the_cache[doc_number]
            }

    def generate_json_schema(self, data):
        '''
        Uses the genson package to introspect json type data and generate the skeleton of a JSON Schema document
        (Draft 6) for further documentation.

        :param data: must be one of the following - python dictionary object, python list of dictionaries, json string
        that can be loaded to a dictionary or list of dictionaries
        :return: json string containing the generated json schema skeleton
        '''
        if isinstance(data, str):
            data = json.loads(data)

        if isinstance(data, dict):
            data = [data]

        if len(data) == 0:
            return "Error: your list of objects (dictionaries) must contain at least one object to process"

        if not isinstance(data[0], dict):
            return "Error: your list must contain a dictionary type object"

        try:
            builder = SchemaBuilder()
            builder.add_schema({"type": "object", "properties": {}})
            for r in data:
                for k, v in r.items():
                    builder.add_object({k: v})
        except Exception as e:
            return f"Error: {e}"

        return builder.to_json()


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
