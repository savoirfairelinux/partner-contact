# -*- coding: utf-8 -*-

import openerp.tests.common as common
from ..model import utils


class test_utils(common.TransactionCase):

    def setUp(self):
        super(test_utils, self).setUp()

    def test_ids_with_inverse(self):
        def assertDoubleListEqual(list1, list2, msg=None):
            self.assertListEqual(list1[0], list2[0], msg)
            self.assertListEqual(list1[1], list2[1], msg)

        assertDoubleListEqual(
            utils.ids_with_inverse([1], []),
            ([1], []),
        )
        assertDoubleListEqual(
            utils.ids_with_inverse([1], [1]),
            ([1], [2]),
        )
        assertDoubleListEqual(
            utils.ids_with_inverse([2], []),
            ([3], []),
        )
        assertDoubleListEqual(
            utils.ids_with_inverse([], [3]),
            ([], [6]),
        )
        assertDoubleListEqual(
            utils.ids_with_inverse([4], []),
            ([7], []),
        )
        assertDoubleListEqual(
            utils.ids_with_inverse([4], [3]),
            ([7], [6]),
        )
        assertDoubleListEqual(
            utils.ids_with_inverse([5], [4]),
            ([9], [8]),
        )
        assertDoubleListEqual(
            utils.ids_with_inverse([1, 2, 5], [2, 4]),
            ([1, 3, 9], [2, 4, 8]),
        )

    def test_both_to_ids(self):
        self.assertListEqual(
            utils.both_to_ids([1]),
            [1]
        )
        self.assertListEqual(
            utils.both_to_ids([2]),
            [1]
        )
        self.assertListEqual(
            utils.both_to_ids([3]),
            [2]
        )
        self.assertListEqual(
            utils.both_to_ids([6]),
            [3]
        )
        self.assertListEqual(
            utils.both_to_ids([1, 3, 2, 4]),
            [1, 2]
        )
        self.assertListEqual(
            utils.both_to_ids([1, 2, 3, 2]),
            [1, 2]
        )
