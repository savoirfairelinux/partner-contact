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
from . import utils


class ResPartnerRelationAll(models.AbstractModel):
    _auto = False
    _log_access = False
    _name = 'res.partner.relation.all'
    _duplicates = 'res.partner.relation'
    _description = 'All (non-inverse + inverse) relations between partners'

    left_partner_id = fields.Many2one(
        'res.partner',
        string='Source Partner',
        required=True,
        auto_join=True,
        ondelete='cascade',
    )
    right_partner_id = fields.Many2one(
        'res.partner',
        string='Destination Partner',
        required=True,
        auto_join=True,
        ondelete='cascade',
    )
    type_id = fields.Many2one(
        'res.partner.relation.type.all',
        string='Type',
        required=True,
        auto_join=True,
    )
    date_start = fields.Date('Starting date')
    date_end = fields.Date('Ending date')
    active = fields.Boolean('Active', default=True)

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        """Map reads from res.partner.relation.all to
        res.partner.relation.type while inversing fields were necessary
        """
        duplicate_pool = self.env[self._duplicates]

        def mapped_read(res_id, fields, direct):
            """Reverse left and right as well as sub name for name_inverse
            Map type_id to a res.partner.relation.type.all
            """

            def map_key(key):
                """Reverse left and right in key"""
                if 'right' in key:
                    key = key.replace('right', 'left')
                elif 'left' in key:
                    key = key.replace('left', 'right')
                return key

            if not direct:
                fields_inv = []
                for f in fields:
                    if f == 'left_partner_id':
                        fields_inv.append('right_partner_id')
                    elif f == 'right_partner_id':
                        fields_inv.append('left_partner_id')
                    else:
                        fields_inv.append(f)
                fields = fields_inv
            duplicate_obj = duplicate_pool.browse(utils.both_to_id(res_id))
            values = duplicate_obj.read(fields)[0]
            if 'type_id' in fields:
                if direct:
                    args = ([values['type_id'][0]], [])
                else:
                    args = ([], [values['type_id'][0]])
                type_ids = utils.ids_with_inverse(*args)
                type_id = (type_ids[0] + type_ids[1])[0]
                type_pool = self.env[self._model._columns['type_id']._obj]
                type_obj = type_pool.browse(type_id)
                values['type_id'] = type_obj.name_get()[0]

            values['id'] = res_id

            if not direct:
                old_value = values.copy()
                values = {
                    map_key(k): v
                    for k, v in old_value.iteritems()
                }

            return values

        direct_ids = filter(utils.id_is_direct, self._ids)
        inverse_ids = set(self._ids).difference(direct_ids)

        res = []
        for i in direct_ids:
            try:
                res.append(mapped_read(i, fields, True))
            except IndexError:
                import ipdb; ipdb.set_trace()
                pass
        for i in inverse_ids:
            try:
                res.append(mapped_read(i, fields, False))
            except IndexError:
                import ipdb; ipdb.set_trace()
                pass
        return res

    @api.model
    @api.returns('self')
    def search(self, args, offset=0, limit=None, order=None, count=False):
        duplicate_pool = self.env[self._duplicates]
        ids = duplicate_pool.search(
            args,
            offset=(offset * utils.PADDING) if offset else offset,
            limit=(limit / utils.PADDING) if limit else limit,
            order=order,
            count=count,
        )
        direct_ids, inverse_ids = utils.ids_with_inverse(ids, ids)
        return self.browse(direct_ids + inverse_ids)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """search for translated names in res.partner.relation.type"""
        import ipdb; ipdb.set_trace()
        duplicate_pool = self.env[self._duplicates]
        direct_ids = duplicate_pool.search(
            [('left_partner_id.name', operator, name)]
        )
        inverse_ids = duplicate_pool.search(
            [('right_partner_id.name', operator, name)],
        )
        all_ids = utils.ids_with_inverse(direct_ids, inverse_ids)
        return [i.name_get() for i in self.browse(all_ids[0] + all_ids[1])]

    @api.multi
    def write(self, vals):
        """divert non-problematic writes to underlying table"""
        # TODO
        import ipdb; ipdb.set_trace()
        return self.env[self._duplicates].write(
            [i / 10 for i in self._ids],
            {k: vals[k] for k in vals if not self._columns[k].readonly}
        )

