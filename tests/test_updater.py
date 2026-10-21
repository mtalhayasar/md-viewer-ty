import unittest

from mdviewer.updater import SETUP_PATTERN, is_newer, parse_version


class UpdaterTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("2.0"), (2, 0, 0))

    def test_newer(self):
        self.assertTrue(is_newer("1.0.1", "1.0.0"))
        self.assertTrue(is_newer("1.10.0", "1.9.9"))
        self.assertFalse(is_newer("1.0.0", "1.0.0"))
        self.assertFalse(is_newer("0.9.0", "1.0.0"))

    def test_setup_asset_name(self):
        self.assertTrue(SETUP_PATTERN.match("MDViewerTY-Setup-1.2.0.exe"))
        self.assertFalse(SETUP_PATTERN.match("MDViewerTY-1.2.0-portable.zip"))


if __name__ == "__main__":
    unittest.main()
