import requests
import xmltodict
from bs4 import BeautifulSoup
from . import bis

bis_utils = bis.Utils()


class Tess:
    def __init__(self):
        self.description = 'Set of functions for working with the USFWS Threatened and Endangered Species System'
        self.tess_api_base = "https://ecos.fws.gov/ecp0/TessQuery?request=query&xquery=/SPECIES_DETAIL"
        self.response_result = bis_utils.processing_metadata()

    def search(self, criteria):

        tess_result = self.response_result
        if criteria.isdigit():
            tess_result["Processing Metadata"]["Search URL"] = f'{self.tess_api_base}[TSN={criteria}]'
        else:
            tess_result["Processing Metadata"]["Search URL"] = f'{self.tess_api_base}[SCINAME="{criteria}"]'

        # Query the TESS XQuery service
        tess_response = requests.get(tess_result["Processing Metadata"]["Search URL"])

        if tess_response.status_code != 200:
            tess_result["Processing Metadata"]["Status"] = f"HTTP Status Code: {tess_response.status_code}"
            return tess_result

        # Build an unordered dict from the TESS XML response (we don't care about ordering for our purposes here)
        tessDict = xmltodict.parse(tess_response.text, dict_constructor=dict)

        if "results" not in tessDict.keys() or tessDict["results"] is None:
            tess_result["Processing Metadata"]["Status"] = "No results"
            return tess_result

        tess_result["Processing Metadata"]["Status"] = "Successful Match"
        tess_result["TESS Species"] = tessDict["results"]

        return tess_result


class Ecos:
    def __init__(self):
        self.property_registry = [
            {
                'Properties': ['Status', 'Date Listed', 'Lead Region', 'Where Listed'],
                'Table Name': 'Current Listing Status Summary'},
            {
                'Properties': ['Date', 'Citation Page', 'Title'],
                'Table Name': 'Federal Register Documents'},
            {
                'Properties': ['Date', 'Citation Page', 'Title'],
                'Table Name': 'Special Rule Publications'},
            {
                'Properties': ['Date', 'Title', 'Plan Action Status', 'Plan Status'],
                'Table Name': 'Current Recovery Plan(s)'},
            {
                'Properties': ['Date', 'Citation Page', 'Title', 'Document Type'],
                'Table Name': 'Other Recovery Documents'},
            {
                'Properties': ['Date', 'Title'],
                'Table Name': 'Five Year Review'},
            {
                'Properties': ['HCP Plan Summaries'],
                'Table Name': 'Habitat Conservation Plans (HCP)'
            }
        ]
        self.description = 'Set of functions for working with other parts of ECOS'
        self.response_result = bis_utils.processing_metadata()

    def extract_js_function_value(self, string):
        return string[string.find('"') + len('"'):string.rfind('"')]

    def itis_tsn(self, ecos_soup):
        try:
            tsn = ecos_soup.find('div', {'class': 'taxonomy new-row'}).findNext('div').findNext('a')['href'].split('=')[-1]
            if tsn:
                return tsn
            else:
                return None
        except:
            return None

    def scrape_ecos(self, ecos_url):
        extracted_data = self.response_result
        extracted_data["Processing Metadata"]["Search URL"] = ecos_url

        page = requests.get(ecos_url)
        soup = BeautifulSoup(page.content, "html.parser")

        if not soup:
            return extracted_data

        extracted_data["Processing Metadata"]["Status"] = "Page Successfully Retrieved"
        extracted_data["ITIS TSN"] = self.itis_tsn(soup)

        html_title = soup.find('title')

        if html_title.text.find('(') > 0:
            extracted_data["Scientific Name"] = html_title.text.split('(')[1].split(')')[0].strip()
            extracted_data["Common Name"] = html_title.text.split('(')[0].replace('Species Profile for', '').strip()
        else:
            extracted_data["Scientific Name"] = html_title.text.replace('Species Profile for', '').strip()
            extracted_data["Common Name"] = None

        for section in soup.findAll('div', {'class': 'table-caption'}):
            table_title = section.text.replace("(learn more)", "").strip()
            next_table = section.findNext('table')
            table_header = next_table.find('thead')
            if table_header is not None:
                this_table = {
                    "Table Name": table_title
                }
                table_props = list()
                for index, prop in enumerate(table_header.select('tr')[0].select('th')):
                    table_props.append(prop.text.strip())
                this_table["Properties"] = table_props

                if next((t for t in self.property_registry if t == this_table), None) is not None:
                    tbody = next_table.find('tbody')
                    if tbody is not None:
                        extracted_data[this_table["Table Name"]] = list()
                        for row in tbody.find_all('tr'):
                            this_record = dict()
                            for i, column in enumerate(row.select('td')):
                                if this_table["Table Name"] == "Status Summary" and \
                                        this_table["Properties"][i] == "Status":
                                    value = self.extract_js_function_value(column.text.strip())
                                else:
                                    value = column.text.strip()

                                this_record[this_table["Properties"][i]] = value

                                if column.find('a'):
                                    this_record[f'{this_table["Properties"][i]}_link'] = column.find('a')["href"]

                            extracted_data[this_table["Table Name"]].append(this_record)

        return extracted_data
