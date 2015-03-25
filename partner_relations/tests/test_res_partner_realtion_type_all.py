# -*- coding: utf-8 -*-

import openerp.tests.common as common


class test_res_partner_realtion_type_all(common.TransactionCase):

    def setUp(self):
        super(test_res_partner_realtion_type_all, self).setUp()

        self.type_all_pool = self.env['res.partner.relation.type.selection']

        self.name = "Is testing"
        self.name_inverse = "Is being tested by"

        self.relation_type = self.env['res.partner.relation.type'].create({
            "name": self.name,
            "name_inverse": self.name_inverse,
            "contact_type_left": "p",
            "contact_type_right": "p",
        })
        self.direct_id = self.type_all_pool.id_to_direct(self.relation_type.id)
        self.inverse_id = self.type_all_pool.id_to_inverse(
            self.relation_type.id
        )
        self.direct_type = self.type_all_pool.browse(self.direct_id)
        self.inverse_type = self.type_all_pool.browse(self.inverse_id)

    def test_read(self):
        self.assertEqual(
            self.direct_type.name,
            self.name
        )
        self.assertEqual(
            self.inverse_type.name,
            self.name_inverse
        )
        self.assertEqual(
            self.direct_type.contact_type_left,
            self.inverse_type.contact_type_right,
        )
        self.assertEqual(
            self.direct_type.contact_type_right,
            self.inverse_type.contact_type_left,
        )
        self.assertEqual(
            self.direct_type.partner_category_left,
            self.inverse_type.partner_category_right,
        )
        self.assertEqual(
            self.direct_type.partner_category_right,
            self.inverse_type.partner_category_left,
        )
        # TODO test a read of name_inverse

    def test_name_get(self):
        direct_id = self.type_all_pool.id_to_direct(self.relation_type.id)
        inverse_id = self.type_all_pool.id_to_inverse(self.relation_type.id)
        self.assertEqual(
            self.relation_type.browse(direct_id).name_get()[0][1],
            self.name,
        )
        self.assertEqual(
            self.relation_type.browse(inverse_id).name_get()[0][1],
            self.name_inverse,
        )

    def test_name_search(self):
        self.assertEqual(
            len(self.type_all_pool.name_search(name="is tes")),
            1,
            "Name search of 'is tes' did not return one and only one result"
        )
        self.assertEqual(
            len(self.type_all_pool.name_search(name="is be")),
            1,
            "Name search of 'is be' did not return one and only one result"
        )
        self.assertEqual(
            len(self.type_all_pool.name_search(name="tested")),
            2,
            "Name search of 'tested' did not return two and only two results"
        )
