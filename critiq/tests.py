#! venv/bin/python
import unittest


class TestWebApp(unittest.TestCase):
    def setUp(self):
        from webapp import app
        self.app = app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        self.assertIn("<!DOCTYPE html>", rv.data)


if __name__ == '__main__':
    unittest.main()
