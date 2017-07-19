import unittest
from app import *

class BottleTestCase(unittest.TestCase):
    """Running tests on our Bottle Application"""
    def test_index_page(self):
        """Test is home page returns a success code"""
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
