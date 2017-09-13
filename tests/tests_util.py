import unittest

from rapide_et_furieux import util


class TestIntersect(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_float(self):
        # failed with those values:
        # ((1146.9914252277613, 670.0558535714817),
        #  (1147.472893500418, 735.0540703801175))
        # ((1023, 694), (1158, 693))
        # because there are float instead of intergers

        line_a = ((1146.9914252277613, 670.0558535714817),
                  (1147.472893500418, 735.0540703801175))
        line_b = ((1023, 694), (1158, 693))
        pt = util.get_segment_intersect_point(line_a, line_b)
        self.assertIsNotNone(pt)


class TestRaytrace(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_raytrace(self):
        r = list(util.raytrace(((256, 635), (322, 815)), 128))
        self.assertEqual(r, [(2, 4), (2, 5), (2, 6)])
