import unittest
from figshare_import.defs import TEST_ARTICLE
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

if __name__ == '__main__':
    unittest.main()