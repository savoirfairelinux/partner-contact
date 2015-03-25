# -*- coding: utf-8 -*-
"""Extend res.partner model"""
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2013 Therp BV (<http://therp.nl>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    relation_left_ids = fields.One2many(
        'res.partner.relation',
        'left_partner_id',
        string='Left Relations',
        selectable=False,
    )
    relation_right_ids = fields.One2many(
        'res.partner.relation',
        'right_partner_id',
        string='Right Relations',
        selectable=False,
    )
    relation_ids = fields.One2many(
        'res.partner.relation',
        compute='_get_relation_ids',
        string='All relations with current partner',
        selectable=False,
    )
    relation_count = fields.Integer(
        'Relation Count',
        compute='_count_relations',
    )

    @api.one
    @api.depends('relation_left_ids', 'relation_right_ids')
    def _get_relation_ids(self):
        """Compute all relations where current partner is left or right of
        relation
        """
        self.relation_ids = self.relation_left_ids + self.relation_right_ids

    @api.one
    @api.depends('relation_ids')
    def _count_relations(self):
        """Count the number of relations this partner has for Smart Button"""
        self.relation_count = len(self.relation_ids)
