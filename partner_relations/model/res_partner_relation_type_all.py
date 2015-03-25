# -*- coding: UTF-8 -*-
"""
Created on 23 may 2014

@author: Ronald Portier, Therp

rportier@therp.nl
http://www.therp.nl

For the model defined here _auto is set to False to prevent creating a
database file. All i/o operations are overridden to use a sql SELECT that
takes data from res_partner_connection_type where each type is included in the
result set twice, so it appears that the connection type and the inverse
type are separate records..

The original function _auto_init is still called because this function
normally (if _auto == True) not only creates the db tables, but it also takes
care of registering all fields in ir_model_fields. This is needed to make
the field labels translatable.

example content for last lines of _statement:
select id, record_type,
  customer_id, customer_name, customer_city, customer_zip, customer_street,
  caller_id, caller_name, caller_phone, caller_fax, caller_email
from FULL_LIST as ResPartnerRelationTypeSelection where record_type = 'c'
ORDER BY ResPartnerRelationTypeSelection.customer_name asc,
ResPartnerRelationTypeSelection.caller_name asc;

"""

from openerp import fields, models, api
from . import utils


class ResPartnerRelationTypeAll(models.AbstractModel):
    """Virtual relation types

    No database entry.
    Creates a direct and inverse relationship for each
    res.partner.relation.type
    It is not meant to be directly accessed
    """

    _auto = False  # Do not try to create table in _auto_init(..)
    _log_access = False
    _name = 'res.partner.relation.type.all'
    _duplicates = 'res.partner.relation.type'
    _description = 'All relation types'
    _foreign_keys = []
    _order = 'name asc'

    name = fields.Char(
        'Name',
        size=128,
        required=True,
        translate=True,
    )
    contact_type_left = fields.Selection(
        '_get_partner_types',
        'Left partner type',
    )
    contact_type_right = fields.Selection(
        '_get_partner_types',
        'Right partner type',
    )
    partner_category_left = fields.Many2one(
        'res.partner.category',
        'Left partner category',
    )
    partner_category_right = fields.Many2one(
        'res.partner.category',
        'Right partner category',
    )

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        """Map reads from res.partner.relation.type.all to
        res.partner.relation.type while inversing fields were necessary
        """
        fields_inv = [f if f != 'name' else f + '_inverse' for f in fields]
        duplicate_pool = self.env[self._duplicates]

        def mapped_read(res_id, direct):
            """Reverse left and right as well as sub name for name_inverse
            """

            def map_key(key):
                """Reverse left and right in key"""
                if 'right' in key:
                    key = key.replace('right', 'left')
                elif 'left' in key:
                    key = key.replace('left', 'right')
                return key

            mapped_fields = fields if direct else map_key(fields_inv)
            value = duplicate_pool.browse(utils.both_to_id(res_id)).read(
                fields=mapped_fields, load=load
            )[0]
            value['id'] = res_id
            if not direct:
                old_value = value.copy()
                value = {
                    map_key(k): v
                    for k, v in old_value.iteritems()
                }
                value['name'] = old_value['name_inverse']
                del value['name_inverse']
            return value

        direct_ids = filter(utils.id_is_direct, self._ids)
        inverse_ids = set(self._ids).difference(direct_ids)

        res = []
        for i in direct_ids:
            try:
                res.append(mapped_read(i, True))
            except IndexError:
                pass
        for i in inverse_ids:
            try:
                res.append(mapped_read(i, False))
            except IndexError:
                pass
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """search for translated names in res.partner.relation.type"""
        duplicate_pool = self.env[self._duplicates]
        direct_ids = duplicate_pool.search(
            [('name', operator, name)]
        )
        inverse_ids = duplicate_pool.search(
            [('name_inverse', operator, name)],
        )
        all_ids = utils.ids_with_inverse(direct_ids, inverse_ids)
        return [i.name_get() for i in self.browse(all_ids[0] + all_ids[1])]
