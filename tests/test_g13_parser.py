import unittest
from unittest.mock import MagicMock
from parsers.g13_parser import Form13GParser

'''python -m tests.test_g13_parser'''
class TestForm13GParser(unittest.TestCase):
    def setUp(self):
        # Mock EdgarClient and LLMClient
        self.mock_client = MagicMock()
        self.mock_llm = MagicMock()
        self.parser = Form13GParser(self.mock_client, self.mock_llm)

    def test_prefilter_html(self):
        html = """
        <html><body>
        <h1>Schedule 13G</h1>
        <table><tr><td>Issuer</td><td>Test Corp</td></tr></table>
        <p>Item 4. Ownership</p>
        <p>Beneficial ownership: 10000</p>
        <p>Signature</p>
        </body></html>
        """
        filtered = self.parser.prefilter_13g_sections(html)
        self.assertIn("Schedule 13G", filtered)
        self.assertIn("Issuer", filtered)
        self.assertIn("Beneficial ownership", filtered)
        self.assertIn("Signature", filtered)

    def test_prefilter_txt(self):
        txt = """Schedule 13G\nIssuer: Test Corp\nItem 4. Ownership\nBeneficial ownership: 10000\nSignature\n"""
        filtered = self.parser.prefilter_13g_sections(txt)
        self.assertIn("Schedule 13G", filtered)
        self.assertIn("Issuer", filtered)
        self.assertIn("Beneficial ownership", filtered)
        self.assertIn("Signature", filtered)

    def test_prefilter_keywords(self):
        txt = """
        Some intro\nCUSIP: No 123456789\nissuer: Test Corp\nreporting person: John Doe\nSignature\n"""
        filtered = self.parser.prefilter_13g_sections(txt)
        self.assertIn("CUSIP", filtered)
        self.assertIn("issuer", filtered)
        self.assertIn("reporting person", filtered)

    def test_fulllength_htm(self):
        # read from test_htm_file.htm
        with open("tests/test_htm_file.htm", "r") as f:
            html = f.read()
            filtered = self.parser.prefilter_13g_sections(html).lower()
            # print("filtered--------------\n", filtered)
            self.assertIn("cusip", filtered)
            self.assertIn("issuer", filtered)
            self.assertIn("reporting persons", filtered)
            self.assertIn("sole voting power", filtered)
            self.assertIn("sole dispositive power", filtered)
            self.assertIn("aggregate amount", filtered)

if __name__ == "__main__":
    unittest.main()
