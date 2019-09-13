from sciencebasepy import SbSession
from . import bis

bis_utils = bis.Utils()


class Search:
    def __init__(self):
        self.sb = SbSession()
        self.params = {
            "max": 1000,
            "fields": "id"
        }
        self.acceptable_system_types = [
            None,
            "Data Release",
            "Folder",
            "Community",
            "Downloadable",
            "Mappable",
            "Map Service"
        ]
        self.acceptable_browse_categories = [
            None,
            "Physical Item",
            "Publication",
            "Data",
            "Project",
            "Image",
            "Map",
            "Data Release - In Progress",
            "Web Site",
            "Collection",
            "Software",
            "Data Release - Under Revision"
        ]

    def search_snapshot(self, system_type=None, browse_category=None, q=None, fields="id"):
        '''
        Function is designed to return a snapshot of ScienceBase items at a point in time with a processing_metadata
        structure we are using in the Biogeographic Information System. It adds a little bit of logic to the
        sciencebasepy API to handle setting up specific filters of interest to our work.

        :param system_type: If not None, accepts one of the available special item types in ScienceBase
        :param browse_category: If not None, accepts one of the available browse category values in ScienceBase
        :param q: query term(s)
        :param fields: Comma delimited string of ScienceBase Item fields to return
        :return: processing_metadata and list of items returned from search
        '''

        result = bis_utils.processing_metadata()
        result["processing_metadata"]["status"] = "failure"
        result["processing_metadata"]["status_message"] = "Search failed"

        if system_type not in self.acceptable_system_types:
            result["processing_metadata"]["status_message"] = \
                f"systemType must be one of: {self.acceptable_system_types}"
            return result

        if browse_category not in self.acceptable_browse_categories:
            result["processing_metadata"]["status_message"] = \
                f"browseCategory must be one of: {self.acceptable_browse_categories}"
            return result

        parameters = {
            "fields": fields,
            "max": self.params["max"]
        }

        filters = list()

        if system_type is not None:
            filters.append(f"systemType={system_type}")

        if browse_category is not None:
            filters.append(f"browseCategory={browse_category}")

        if len(filters) > 0:
            for index, filter in enumerate(filters):
                parameters[f"filter{index}"] = filter

        if q is not None:
            parameters["q"] = q

#        try:
        items = self.sb.find_items(parameters)
        result["processing_metadata"]["api"] = items['selflink']['url']
        result["parameters"] = parameters
        if len(items['items']) == 0:
            result["processing_metadata"]["status"] = "success"
            result["processing_metadata"]["status_message"] = "no items found"
            return result
        else:
            result["data"] = list()
            while items and 'items' in items:
                result["data"].extend(items['items'])
                items = self.sb.next(items)
            result["processing_metadata"]["status"] = "success"
            result["processing_metadata"]["status_message"] = f'Number items found: {len(result["data"])}'
            return result

#        except Exception as e:
#            result["processing_metadata"]["status"] = "error"
#            result["processing_metadata"]["status_message"] = e
#            return result
