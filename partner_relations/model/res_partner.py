# -*- coding: utf-8 -*-
'''Extend res.partner model'''
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

import time
from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp.osv.expression import is_leaf, AND, OR, FALSE_LEAF


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
    search_relation_id = fields.Many2one(
        'res.partner.relation.type.selection',
        compute=lambda self, *args: {i: False for i in self._ids},
        search='_search_relation_id',
        string='Has relation of type',
    )
    search_relation_partner_id = fields.Many2one(
        'res.partner',
        compute=lambda self, *args: {i: False for i in self._ids},
        search='_search_related_partner_id',
        string='Has relation with',
    )
    search_relation_date = fields.Date(
        compute=lambda self, *args: {i: False for i in self._ids},
        search='_search_relation_date',
        string='Relation valid',
    )
    search_relation_partner_category_id = fields.Many2one(
        'res.partner.category',
        compute=lambda self, *args: {i: False for i in self._ids},
        search='_search_related_partner_category_id',
        string='Has relation with a partner in category',
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

    def _search_relation_id(self, operator, operand):
        result = []
        import ipdb; ipdb.set_trace()
        for arg in args:
            if isinstance(arg, tuple) and arg[0] == name:
                if arg[1] not in ['=', '!=', 'like', 'not like', 'ilike',
                                  'not ilike', 'in', 'not in']:
                    raise orm.except_orm(
                        _('Error'),
                        _('Unsupported search operand "%s"') % arg[1])

                relation_type_selection_ids = []
                relation_type_selection = self\
                    .pool['res.partner.relation.type.selection']

                if arg[1] == '=' and isinstance(arg[2], (long, int)):
                    relation_type_selection_ids.append(arg[2])
                elif arg[1] == '!=' and isinstance(arg[2], (long, int)):
                    type_id, is_inverse = relation_type_selection\
                        .get_type_from_selection_id(
                            cr, uid, arg[2])
                    result = OR([
                        result,
                        [
                            ('relation_all_ids.type_id', '!=', type_id),
                        ]
                    ])
                    continue
                else:
                    relation_type_selection_ids = relation_type_selection\
                        .search(
                            cr, uid,
                            [
                                ('type_id.name', arg[1], arg[2]),
                                ('record_type', '=', 'a'),
                            ],
                            context=context)
                    relation_type_selection_ids.extend(
                        relation_type_selection.search(
                            cr, uid,
                            [
                                ('type_id.name_inverse', arg[1], arg[2]),
                                ('record_type', '=', 'b'),
                            ],
                            context=context))

                if not relation_type_selection_ids:
                    result = AND([result, [FALSE_LEAF]])

                for relation_type_selection_id in relation_type_selection_ids:
                    type_id, is_inverse = relation_type_selection\
                        .get_type_from_selection_id(
                            cr, uid, relation_type_selection_id)

                    result = OR([
                        result,
                        [
                            '&',
                            ('relation_all_ids.type_id', '=', type_id),
                            ('relation_all_ids.record_type', '=',
                             'b' if is_inverse else 'a')
                        ],
                    ])

        return result

    def _search_relation_date(self, operator, operand):
        result = []
        import ipdb; ipdb.set_trace()
        for arg in args:
            if isinstance(arg, tuple) and arg[0] == name:
                # TODO: handle {<,>}{,=}
                if arg[1] != '=':
                    continue

                result.extend([
                    '&',
                    '|',
                    ('relation_all_ids.date_start', '=', False),
                    ('relation_all_ids.date_start', '<=', arg[2]),
                    '|',
                    ('relation_all_ids.date_end', '=', False),
                    ('relation_all_ids.date_end', '>=', arg[2]),
                ])

        return result

    def _search_related_partner_id(self, operator, operand):
        result = []
        import ipdb; ipdb.set_trace()
        for arg in args:
            if isinstance(arg, tuple) and arg[0] == name:
                result.append(
                    (
                        'relation_all_ids.other_partner_id',
                        arg[1],
                        arg[2],
                    ))

        return result

    def _search_related_partner_category_id(self, operator, operand):
        result = []
        import ipdb; ipdb.set_trace()
        for arg in args:
            if isinstance(arg, tuple) and arg[0] == name:
                result.append(
                    (
                        'relation_all_ids.other_partner_id.category_id',
                        arg[1],
                        arg[2],
                    ))

        return result

    @api.one
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default.setdefault('relation_ids', [])
        default.setdefault('relation_all_ids', [])
        return super(ResPartner, self).copy_data(default=default)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # inject searching for current relation date if we search for relation
        # properties and no explicit date was given
        date_args = []
        for arg in args:
            if is_leaf(arg) and arg[0].startswith('search_relation'):
                if arg[0] == 'search_relation_date':
                    date_args = []
                    break
                if not date_args:
                    date_args = [
                        ('search_relation_date', '=', time.strftime(
                            DEFAULT_SERVER_DATE_FORMAT))]

        # because of auto_join, we have to do the active test by hand
        active_args = []
        if self._context.get('active_test', True):
            for arg in args:
                if is_leaf(arg) and\
                        arg[0].startswith('search_relation'):
                    active_args = [('relation_all_ids.active', '=', True)]
                    break

        return super(ResPartner, self).search(
            args + date_args + active_args, offset=offset, limit=limit,
            order=order, count=count
        )

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        """Call read with modified context"""
        self_contextualized = self.with_context(
            self._update_context(self._context, self._ids)
        )
        return super(ResPartner, self_contextualized).read(
            fields=fields, load=load
        )

    @api.multi
    def write(self, vals):
        """Call write with modified context"""
        self_contextualized = self.with_context(
            self._update_context(self._context, self._ids)
        )
        return super(ResPartner, self_contextualized).write(vals)

    def _update_context(self, context, ids):
        if context is None:
            context = {}
        ids = ids if isinstance(ids, list) else [ids] if ids else []
        result = context.copy()
        result.setdefault('active_id', ids[0] if ids else None)
        result.setdefault('active_ids', ids)
        result.setdefault('active_model', self._name)
        return result
