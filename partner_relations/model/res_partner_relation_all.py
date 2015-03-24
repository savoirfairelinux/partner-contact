# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Therp BV (<http://therp.nl>).
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

from openerp import models, fields, api
from openerp.tools import drop_view_if_exists
from .res_partner_relation_type_selection import (
    ResPartnerRelationTypeSelection,
)


class ResPartnerRelationAll(models.Model):
    _auto = False
    _log_access = False
    _name = 'res.partner.relation.all'
    _description = 'All (non-inverse + inverse) relations between partners'

    _additional_view_fields = []
    '''append to this list if you added fields to res_partner_relation that
    you need in this model and related fields are not adequate (ie for sorting)
    You must use the same name as in res_partner_relation.
    Don't overwrite this list in your declaration but append in _auto_init:

    def _auto_init(self, cr, context=None):
        self._additional_view_fields.append('my_field')
        return super(ResPartnerRelationAll, self)._auto_init(
            cr, context=context)

    _columns = {
        'my_field': ....
    }
    '''

    def _auto_init(self, cr, context=None):
        drop_view_if_exists(cr, self._table)
        additional_view_fields = ','.join(self._additional_view_fields)
        additional_view_fields = (',' + additional_view_fields)\
            if additional_view_fields else ''
        cr.execute(
            '''create or replace view %s as
            select
                id * 10 as id,
                id as relation_id,
                type_id,
                cast('a' as char(1)) as record_type,
                left_partner_id as this_partner_id,
                right_partner_id as other_partner_id,
                date_start,
                date_end,
                active,
                type_id * 10 as type_selection_id
                %s
            from res_partner_relation
            union select
                id * 10 + 1,
                id,
                type_id,
                cast('b' as char(1)),
                right_partner_id,
                left_partner_id,
                date_start,
                date_end,
                active,
                type_id * 10 + 1
                %s
            from res_partner_relation''' % (
                self._table,
                additional_view_fields,
                additional_view_fields,
            )
        )

        return super(ResPartnerRelationAll, self)._auto_init(
            cr, context=context)

    record_type = fields.Selection(
        lambda *a, **kw: (
            ResPartnerRelationTypeSelection._get_record_types()
        ),
        'Record type',
        readonly=True
    )
    relation_id = fields.Many2one(
        'res.partner.relation',
        'Relation',
        readonly=True,
    )
    type_id = fields.Many2one(
        'res.partner.relation.type',
        'Relation type',
        readonly=True,
    )
    type_selection_id = fields.Many2one(
        'res.partner.relation.type.selection',
        'Relation type',
        readonly=True,
    )
    this_partner_id = fields.Many2one(
        'res.partner',
        'Current partner',
        readonly=True,
    )
    other_partner_id = fields.Many2one(
        'res.partner',
        'Other partner',
        readonly=True,
    )
    date_start = fields.Date('Starting date')
    date_end = fields.Date('Ending date')
    active = fields.Boolean('Active')

    @api.multi
    @api.depends('this_partner_id')
    def name_get(self):
        return [
            (this.id, '%s %s %s' % (
                this.this_partner_id.name,
                this.type_selection_id.name_get()[0][1],
                this.other_partner_id.name,
            ))
            for this in self
        ]

    @api.multi
    def write(self, vals):
        """divert non-problematic writes to underlying table"""
        return self.env['res.partner.relation'].write(
            [i / 10 for i in self._ids],
            {k: vals[k] for k in vals if not self._columns[k].readonly}
        )
