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
from openerp.tools import drop_view_if_exists
from .res_partner_relation_type import ResPartnerRelationType


class ResPartnerRelationTypeSelection(models.Model):
    """Virtual relation types"""

    _auto = False  # Do not try to create table in _auto_init(..)
    _log_access = False
    _name = 'res.partner.relation.type.selection'
    _description = 'All relation types'
    _foreign_keys = []
    _order = 'name asc'

    record_type = fields.Selection("_get_record_types", 'Record type', size=16)
    type_id = fields.Many2one(
        'res.partner.relation.type',
        'Type',
    )
    name = fields.Char('Name', size=64)
    contact_type_this = fields.Selection(
        ResPartnerRelationType._get_partner_types.im_func,
        "Current record's partner type",
    )
    contact_type_other = fields.Selection(
        ResPartnerRelationType._get_partner_types.im_func,
        "Other record's partner type",
    )
    partner_category_this = fields.Many2one(
        'res.partner.category',
        "Current record's category",
    )
    partner_category_other = fields.Many2one(
        'res.partner.category',
        "Other record's category",
    )
    # search field to handle many2many deltas from the client
    search_partner_category_this = fields.Many2many(
        'res.partner.category',
        compute=lambda self: {i: False for i in self._ids},
        search="_search_partner_category_this",
        type='many2many',
        string="Current record's category",
    )

    @staticmethod
    def _get_record_types():
        return ('a', 'Type'), ('b', 'Inverse type'),

    @api.model
    def get_type_from_selection_id(self, selection_id):
        """Selection id ic computed from id of underlying type and the
        kind of record. This function does the inverse computation to give
        back the original type id, and about the record type.
        """
        type_id = selection_id / 10
        is_reverse = (selection_id % 10) > 0
        return type_id, is_reverse

    def _auto_init(self, cr, context=None):
        drop_view_if_exists(cr, self._table)
        # TODO: we lose field value's translations here.
        # probably we need to patch ir_translation.get_source for that
        # to get res_partner_relation_type's translations
        cr.execute(
            '''create or replace view %s as
            select
                id * 10 as id,
                id as type_id,
                cast('a' as char(1)) as record_type,
                name as name,
                contact_type_left as contact_type_this,
                contact_type_right as contact_type_other,
                partner_category_left as partner_category_this,
                partner_category_right as partner_category_other
            from res_partner_relation_type
            union select
                id * 10 + 1,
                id,
                cast('b' as char(1)),
                name_inverse,
                contact_type_right,
                contact_type_left,
                partner_category_right,
                partner_category_left
             from res_partner_relation_type''' % self._table)

        return super(ResPartnerRelationTypeSelection, self)._auto_init(
            cr, context=context)

    @api.model
    def _search_partner_category_this(self, field_name, args):
        category_ids = []

        for arg in args:
            if isinstance(arg, tuple) and arg[0] == field_name\
                    and (arg[1] == '=' or arg[1] == 'in'):
                # TODO don't we have an api function to eval that?
                for delta in arg[2]:
                    if delta[0] == 6:
                        category_ids.extend(delta[2])

        if category_ids:
            return [
                '|',
                ('partner_category_this', '=', False),
                ('partner_category_this', 'in', category_ids),
            ]
        else:
            return [('partner_category_this', '=', False)]
    @api.multi
    @api.depends('name', 'date_begin', 'date_end')
    def name_get(self):
        'translate name using translations from res.partner.relation.type'
        result = super(ResPartnerRelationTypeSelection, self).name_get()
        ir_translation = self.env['ir.translation']
        return [
            (
                i,
                ir_translation._get_source(
                    'res.partner.relation.type,name_inverse'
                    if self.get_type_from_selection_id(i)[1]
                    else 'res.partner.relation.type,name',
                    'model',
                    self._context.get('lang'),
                    name
                )
            )
            for i, name in result
        ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        'search for translated names in res.partner.relation.type'
        res_partner_relation_type = self.env['res.partner.relation.type']
        relation_ids = res_partner_relation_type.search(
            [('name', operator, name)]
        )
        inverse_relation_ids = res_partner_relation_type.search(
            [('name_inverse', operator, name)],
        )
        all_ids = self.search(
            [
                ('id', 'in',
                 map(lambda x: x.id * 10, relation_ids) +
                 map(lambda x: x.id * 10 + 1, inverse_relation_ids)),
            ] + (args or []),
            limit=limit
        )
        return [i.name_get() for i in all_ids]
