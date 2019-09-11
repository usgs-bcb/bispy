import sciencebasepy
from . import bis

bis_utils = bis.Utils()

class Search:
    def __init__(self):
        self.sbpy = sciencebasepy.SbSession()
        self.params = {}

    #Could add param function to open up search a bit?
    #def update_params(self, search_term, filter="", max=100, fields="id"):
    #    self.params = {"q":search_term, "max":max, "filter":filter, "fields": fields}

    def data_release_search(self, search_term, max="100", fields="id"):
        '''
        Searches for official ScienceBase data releases and returns json structure of search result.
        This function handles the issue of looping through the ScienceBase pagination when you need to 
        get more items than the maximum that can be returned.

        :param search_term: search term that helps identify data release items of interest
        :param fields: Comma delimited string of ScienceBase Item fields to return
        :return: Data release items that are officially recognized by ScienceBase returned from search
        '''
        
        filter_data_release = "systemType=Data Release" 
        self.params = {"q":search_term, "max":"100", "filter":filter_data_release, "fields": fields}
        result = self.search()
        return result
    
    def in_progress_data_release_search(self, search_term, fields="id"):
        '''
        Searches for official ScienceBase data releases that are in progress and returns json structure of search result.
        This function handles the issue of looping through the ScienceBase pagination when you need to 
        get more items than the maximum that can be returned.

        :param search_term: search term that helps identify data release items of interest
        :param fields: Comma delimited string of ScienceBase Item fields to return
        :return: Data release items that are officially recognized by ScienceBase returned from search
        '''
        
        filter_data_release = "browseCategory=Data Release - In Progress" 
        self.params = {"q":search_term, "max":100, "filter":filter_data_release, "fields": fields}
        result = self.search()
        return result

    def search(self):
        '''
        Loops through ScienceBase data release items to return all items meeting specified params.  
        This includes both official ScienceBase data releases and those in progress.
        This function handles the issue of looping through the ScienceBase pagination when you need to 
        get more items than the maximum that can be returned.

        :param search_term: search term that helps identify data release items of interest
        :param fields: Comma delimited string of ScienceBase Item fields to return
        :return: Data release items that are officially recognized by ScienceBase returned from search
        '''
        item_list = []

        result = bis_utils.processing_metadata()
        result["processing_metadata"]["status"] = "failure"
        result["processing_metadata"]["status_message"] = "Search failed"
        
        params = self.params
        
        try: 
            items = self.sbpy.find_items(params)
            result["processing_metadata"]["api"] = items['selflink']['url']
            result["parameters"] = params
            if len(items['items']) == 0:
                result["processing_metadata"]["status"] = "success"
                result["processing_metadata"]["status_message"] = "No official ScienceBase data realeases"
                #Do we want to capture null returns as result['data']=[] or not include 
                return result
            else:
                while items and 'items' in items:
                    item_list.extend(items['items'])
                    items = self.sbpy.next(items)
                num_results = f'{len(item_list)} official ScienceBase data realeases'
                result["processing_metadata"]["status"] = "success"
                result["processing_metadata"]["status_message"] = num_results
                result["data"] = item_list
                return result

        except:
            result["processing_metadata"]["status"] = "failure"
            return result