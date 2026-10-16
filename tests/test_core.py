import unittest
from groupctl.cli import COMMON, TYPES

class ContractSmokeTest(unittest.TestCase):
    def test_event_types(self):
        self.assertEqual(len(TYPES),10)
        self.assertIn('integration_result',TYPES)
    def test_common_fields(self):
        self.assertIn('related_events',COMMON)
        self.assertIn('event_id',COMMON)

if __name__=='__main__':unittest.main()
