import requests
from datetime import datetime
import json
import geopandas as gpd
import bis


class Gap:
    def __init__(self):
        self.gap_species_collection = "527d0a83e4b0850ea0518326"
        self.sb_api_root = "https://www.sciencebase.gov/catalog/items"
        self.sb_geoserver = "https://www.sciencebase.gov/geoserver/CONUS_Range_2001v1/ows"
        self.response_result = bis.response_result()

    def gap_species_search(self, criteria):
        '''
        This function looks for a GAP species in the core habitat maps collection in ScienceBase. If it finds a match,
        it assembles a combined GAP species document from available information in ScienceBase. This includes the basic
        metadata in the item (identifiers, names, etc.), the database parameters file, a cached set of ITIS
        information, and links to habitat map and range map items and services. In addition, the total bounding box
        for all seasons is calculated by retrieving the WFS feature for the range map. This provides a basic idea of
        the geospatial coverage to be expected for a species.

        :param criteria: Can be one of scientific name, common name, ITIS TSN, or GAP species code
        :return: Dictionary containing at least the processing metadata (date/time and URL used) and will contain a GAP
        Species document with all the information assembled for the given species.
        '''

        gap_result = self.response_result
        gap_result["Processing Metadata"]["Summary Result"] = "Not Matched"

        identifier_param = {
            "key": criteria
        }
        gap_result["Processing Metadata"]["Search URL"] = \
            f"{self.sb_api_root}?parentId={self.gap_species_collection}" \
            f"&format=json&fields=identifiers,files,webLinks,distributionLinks&filter=itemIdentifier%3D{identifier_param}"

        sb_result = requests.get(gap_result["Processing Metadata"]["Search URL"]).json()

        if sb_result["total"] == 1:

            gap_result["GAP Species"] = dict()
            gap_result["GAP Species"]["GAP Habitat Map Item"] = sb_result["items"][0]["link"]["url"]
            gap_result["GAP Species"]["GAP Range Map Item"] = next((
                l["uri"] for l in sb_result["items"][0]["webLinks"] if l["title"].find("Range Map") != -1
            ), None)
            gap_result["GAP Species"]["GAP Habitat Map WMS"] = next((
                l["uri"] for l in sb_result["items"][0]["distributionLinks"] if l["title"] == "External WMS Service"
            ), None)
            gap_result["GAP Species"]["GAP Modeling Database Parameters URL"] = next((
                f["url"] for f in sb_result["items"][0]["files"] if f["title"] ==
                                                                    "Machine Readable Habitat Database Parameters"
            ), None)
            gap_result["GAP Species"]["GAP ITIS Information URL"] = next((
                f["url"] for f in sb_result["items"][0]["files"] if f["title"] == "ITIS Information"
            ), None)

            gap_result["GAP Species"]["GAP Habitat Map File Size"] = next((
                f["size"] for f in sb_result["items"][0]["files"] if f["title"] ==
                                                                    "Habitat Map Raster Data"
            ), None)

            sb_range_map_item = requests.get(
                f"{gap_result['GAP Species']['GAP Range Map Item']}?format=json&fields=distributionLinks"
            ).json()

            gap_result["GAP Species"]["GAP Range Map WMS"] = next((
                l["uri"] for l in sb_range_map_item["distributionLinks"] if l["title"] == "External WMS Service"
            ), None)

            for i in sb_result["items"][0]["identifiers"]:
                gap_result["GAP Species"][i["type"]] = i["key"]

            if gap_result["GAP Species"]["GAP Modeling Database Parameters URL"] is not None:
                gap_result["GAP Species"]["GAP Modeling Database Parameters"] = json.loads(
                    requests.get(
                        gap_result["GAP Species"]["GAP Modeling Database Parameters URL"]
                    ).text
                )

            if gap_result["GAP Species"]["GAP ITIS Information URL"] is not None:
                gap_result["GAP Species"]["GAP ITIS Information"] = json.loads(
                    requests.get(
                        gap_result["GAP Species"]["GAP ITIS Information URL"]
                    ).text
                )

            gap_result["GAP Species"]["Range Bounding Box"] = self.gap_spp_range_bbox(
                gap_result["GAP Species"]["GAP_SpeciesCode"]
            )

        return gap_result

    def gap_spp_range_bbox(self, sppcode):
        '''
        Queries the WFS for a given GAP species range and returns the total bounding box (all seasons) for the species.

        :param sppcode: GAP Species Code
        :return: Simple bounding box in a list in EPSG:4326
        '''
        params = dict(
            service="WFS",
            version="1.0.0",
            request="GetFeature",
            typeName="CONUS_Range_2001v1:Species_CONUS_Range_2001v1",
            outputFormat="json",
            CQL_FILTER=f"SppCode='{sppcode}'"
        )

        q = requests.Request("GET", self.sb_geoserver, params=params).prepare().url

        spp_range = gpd.read_file(q)
        spp_range = spp_range.to_crs({"init": "epsg:4326"})

        return spp_range.total_bounds.tolist()
