import unittest
from boddle import boddle
from app import *

class BottleTestCase(unittest.TestCase):
    """Running tests on our Bottle Application"""
    def test_index_page(self):
        """Test if home page returns a success code"""
        # response = test_app.get('/', content_type='html/text')
        self.assertEqual(app.server_static(), True)
        # self.assertEqual(server_static(), 'derek')


if __name__ == '__main__':
    unittest.main()
