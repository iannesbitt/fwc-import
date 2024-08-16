import unittest
from figshare_import.conv import figshare_to_eml

class TestFigshareToEML(unittest.TestCase):
    def setUp(self):
        """
        Set up the test case with the test article.
        """
        self.test_article = TEST_ARTICLE

    def test_conversion_to_eml(self):
        """
        Test the conversion of a figshare article to EML.
        """
        # Perform the conversion
        eml_result = figshare_to_eml(self.test_article)
        # Verify the conversion
        self.assertIn('<eml:eml', eml_result)
        self.assertIn('<dataset>', eml_result)
        self.assertIn('<title>', eml_result)
        self.assertIn(self.test_article['title'], eml_result)
        self.assertIn('<creator>', eml_result)
        self.assertIn(self.test_article['authors'][0]['full_name'], eml_result)
        self.assertIn('<abstract>', eml_result)
        self.assertIn(self.test_article['description'], eml_result)
        if 'keywords' in self.test_article:
            for keyword in self.test_article['keywords']:
                self.assertIn(keyword, eml_result)
        self.assertIn('<pubDate>', eml_result)
        self.assertIn(self.test_article['publication_date'], eml_result)


TEST_ARTICLE = {
      "files": [
        {
          "id": 44937931,
          "name": "BayofPanama_Site1.zip",
          "size": 19891019,
          "is_link_only": False,
          "download_url": "https://ndownloader.figshare.com/files/44937931",
          "supplied_md5": "36fbce3d5c4ddd63c91a69801b6d15d2",
          "computed_md5": "36fbce3d5c4ddd63c91a69801b6d15d2",
          "mimetype": "application/zip"
        }
      ],
      "custom_fields": [],
      "authors": [
        {
          "id": 7540937,
          "full_name": "Steven Paton",
          "is_active": True,
          "url_name": "Steven_Paton",
          "orcid_id": "0000-0003-2035-6699"
        }
      ],
      "figshare_url": "https://smithsonian.figshare.com/articles/dataset/Bay_of_Panama_Water_Quality_Monitoring_Project_Site_1_of_7/10042703",
      "download_disabled": False,
      "description": "<div>Bay of Panama water quality monitoring program. Site #1 (of 7). <br></div><div>Location: 8° 38.743'N, 79° 2.887'W<br></div>Weekly depth profile (approximately 5m intervals) using YSI EXO 2 sonde. <br>Parameters measured temperature, salinity, conductivity, pH, turbidity, chlorophyll, Dissolved Oxygen<p><br>8.994410°, -79.543000°<br>8.910718°N, -79.528919°<br>7° 38.422'N, 81° 42.079'W<br>9°9'42.36\"N, 79°50'15.67\"W<br>0°41′ S latitude, 76°24′ W longitude<br>8° 38.743'N    79° 2.887'W<br>Location: 7.69633 -81.61603</p>",
      "funding": None,
      "funding_list": [],
      "version": 5,
      "status": "public",
      "size": 19891019,
      "created_date": "2024-03-08T14:44:22Z",
      "modified_date": "2024-03-08T14:44:22Z",
      "is_public": True,
      "is_confidential": False,
      "is_metadata_record": False,
      "confidential_reason": "",
      "metadata_reason": "",
      "license": {
        "value": 1,
        "name": "CC BY 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/"
      },
      "tags": [
        "temperature",
        "salinity",
        "turbidity measurement",
        "chlorophyll",
        "conductivity",
        "Acidity",
        "Dissolved Oxygen",
        "Dissolved organic matter (DOM)",
        "Environmental Monitoring",
        "Physical Oceanography"
      ],
      "categories": [
        {
          "id": 26935,
          "title": "Environmental assessment and monitoring",
          "parent_id": 26929,
          "path": "/26863/26929/26935",
          "source_id": "410402",
          "taxonomy_id": 100
        },
        {
          "id": 25906,
          "title": "Physical oceanography",
          "parent_id": 25897,
          "path": "/25717/25897/25906",
          "source_id": "370803",
          "taxonomy_id": 100
        }
      ],
      "references": [
        "https://biogeodb.stri.si.edu/physical_monitoring/research/waterquality"
      ],
      "has_linked_file": False,
      "citation": "Paton, Steve (2019). Bay of Panama Water Quality Monitoring Project, Site 1 of 7. Smithsonian Tropical Research Institute. Dataset. https://doi.org/10.25573/data.10042703.v5",
      "related_materials": [
        {
          "id": 113195580,
          "identifier": "https://biogeodb.stri.si.edu/physical_monitoring/research/waterquality",
          "title": "",
          "relation": "References",
          "identifier_type": "URL",
          "is_linkout": False,
          "link": "https://biogeodb.stri.si.edu/physical_monitoring/research/waterquality"
        }
      ],
      "is_embargoed": False,
      "embargo_date": None,
      "embargo_type": "file",
      "embargo_title": "",
      "embargo_reason": "",
      "embargo_options": [],
      "id": 10042703,
      "title": "Bay of Panama Water Quality Monitoring Project, Site 1 of 7",
      "doi": "10.25573/data.10042703.v5",
      "handle": "",
      "url": "https://api.figshare.com/v2/articles/10042703",
      "published_date": "2024-03-08T14:44:22Z",
      "thumb": "",
      "defined_type": 3,
      "defined_type_name": "dataset",
      "group_id": 23486,
      "url_private_api": "https://api.figshare.com/v2/account/articles/10042703",
      "url_public_api": "https://api.figshare.com/v2/articles/10042703",
      "url_private_html": "https://figshare.com/account/articles/10042703",
      "url_public_html": "https://smithsonian.figshare.com/articles/dataset/Bay_of_Panama_Water_Quality_Monitoring_Project_Site_1_of_7/10042703",
      "timeline": {
        "posted": "2024-03-08T14:44:22",
        "firstOnline": "2019-10-28T12:51:31"
      },
      "resource_title": None,
      "resource_doi": None
    }
"""
An example Figshare metadata dictionary.
"""


if __name__ == '__main__':
    unittest.main()