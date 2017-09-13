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

    def test_horizontal(self):
        line_a = ((256, 635), (322, 815))
        line_b = ((256, 767), (383, 767))
        pt = util.get_segment_intersect_point(line_a, line_b)
        self.assertIsNotNone(pt)

    def test_almost_vertical(self):
        line_a = ((960, 704), (958, 864))
        line_b = ((769, 896), (1025, 769))
        pt = util.get_segment_intersect_point(line_a, line_b)
        self.assertIsNotNone(pt)

    def test_almost_vertical2(self):
        line_a = ((960, 704), (958, 864))
        line_b = ((1025, 769), (897, 832, 5))
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
