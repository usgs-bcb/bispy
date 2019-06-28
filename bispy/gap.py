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
        gap_result= {}
        gap_result["Processing Metadata"] = {
            "Date Processed": datetime.utcnow().isoformat(),
            "Summary Result": "Not Matched"
        }

        identifier_param = {
            "key": criteria
        }
        gap_result["Processing Metadata"]["Search URL"] = \
            f"{self.sb_api_root}?parentId={self.gap_species_collection}" \
            f"&format=json&fields=identifiers,files,webLinks,distributionLinks,dates" \
            f"&filter=itemIdentifier%3D{identifier_param}"

        sb_result = requests.get(gap_result["Processing Metadata"]["Search URL"]).json()

        if sb_result["total"] == 1:
            gap_result["GAP Species"] = self.package_gap_species(self.package_habmap_item(sb_result["items"][0]))

        return gap_result

    def package_habmap_item(self, habmap_item):
        item = {
            "GAP Habitat Map Item": habmap_item["link"]["url"],
            "GAP Range Map Item": next((
                l["uri"] for l in habmap_item["webLinks"] if l["title"].find("Range Map") != -1
            ), None),
            "GAP Habitat Map WMS": next((
                l["uri"] for l in habmap_item["distributionLinks"] if "title" in l.keys() and
                                                                      l["title"] == "External WMS Service"
            ), None),
            "GAP Modeling Database Parameters URL": next((
                f["url"] for f in habmap_item["files"] if "title" in f.keys() and
                                                          f["title"] == "Machine Readable Habitat Database Parameters"
            ), None),
            "GAP ITIS Information URL": next((
                f["url"] for f in habmap_item["files"] if "title" in f.keys() and f["title"] == "ITIS Information"
            ), None),
            "GAP Habitat Map File Size": next((
                f["size"] for f in habmap_item["files"] if "title" in f.keys() and
                                                           f["title"] == "Habitat Map Raster Data"
            ), None),
            "GAP Habitat Map Last Updated": next((
                d["dateString"] for d in habmap_item["dates"] if d["type"] == "lastUpdated"
            ), None)
        }

        for i in habmap_item["identifiers"]:
            item[i["type"]] = i["key"]

        return item

    def package_rangemap_item(self, sppcode, rangemap_url):
        sb_range_map_item = requests.get(
            f"{rangemap_url}?format=json&fields=distributionLinks"
        ).json()

        rangemap_package = dict()
        rangemap_package["GAP Range Map WMS"] = next((
            l["uri"] for l in sb_range_map_item["distributionLinks"] if l["title"] == "External WMS Service"
        ), None)

        rangemap_package["Range Bounding Box"] = self.gap_spp_range_bbox(sppcode)

        return rangemap_package

    def package_gap_species(self, hab_map_package):
        hab_map_package.update(
            self.package_rangemap_item(
                sppcode=hab_map_package["GAP_SpeciesCode"],
                rangemap_url=hab_map_package["GAP Range Map Item"]
            )
        )

        if hab_map_package["GAP Modeling Database Parameters URL"] is not None:
            hab_map_package["GAP Modeling Database Parameters"] = json.loads(
                requests.get(
                    hab_map_package["GAP Modeling Database Parameters URL"]
                ).text
            )

        if hab_map_package["GAP ITIS Information URL"] is not None:
            hab_map_package["GAP ITIS Information"] = json.loads(
                requests.get(
                    hab_map_package["GAP ITIS Information URL"]
                ).text
            )

        return hab_map_package

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

