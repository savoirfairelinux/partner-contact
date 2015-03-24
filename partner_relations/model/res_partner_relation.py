# -*- coding: utf-8 -*-
"""Define model res.partner.relation"""
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

from openerp import models, fields, api, exceptions, _


class ResPartnerRelation(models.Model):
    """Model res.partner.relation is used to describe all links or relations
    between partners in the database.

    In many parts of the code we have to know whether the active partner is
    the left partner, or the right partner. If the active partner is the
    right partner we have to show the inverse name.

    Because the active partner is crucial for the working of partner
    relationships, we make sure on the res.partner model that the partner id
    is set in the context where needed.
    """
    _name = 'res.partner.relation'
    _description = 'Partner Relation'
    _order = 'active desc, date_start desc, date_end desc'

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
        'res.partner.relation.type',
        string='Type',
        required=True,
        auto_join=True,
    )
    date_start = fields.Date('Starting date')
    date_end = fields.Date('Ending date')
    type_selection_id = fields.Many2one(
        'res.partner.relation.type.selection',
        compute='_get_computed_fields',
        multi="computed_fields",
        inverse=lambda *args: None,
        string='Type',
    )
    partner_id_display = fields.Many2one(
        'res.partner',
        compute="_get_computed_fields",
        multi="computed_fields",
        inverse=lambda *args: None,
        string='Partner'
    )
    is_relation_expired = fields.Boolean(
        compute="_get_computed_fields",
        multi="computed_fields",
        method=True,
        string='Relation is expired',
    )
    is_relation_future = fields.Boolean(
        compute="_get_computed_fields",
        multi="computed_fields",
        method=True,
        string='Relation is in the future',
    )
    active = fields.Boolean('Active', default=True)

    @api.one
    def _on_right_partner(self):
        """Determine whether functions are called in a situation where the
        active partner is the right partner. Default False!
        """
        return (
            self._context and
            'active_ids' in self._context and
            self.id in self._context.get('active_ids', [])
        )

    @api.model
    def _correct_vals(self, vals):
        """Fill type and left and right partner id, according to whether
        we have a normal relation type or an inverse relation type
        """
        vals = vals.copy()
        # If type_selection_id ends in 1, it is a reverse relation type
        if 'type_selection_id' in vals:
            prts_model = self.env['res.partner.relation.type.selection']
            type_selection_id = vals['type_selection_id']
            (type_id, is_reverse) = (
                prts_model.get_type_from_selection_id(type_selection_id))
            vals['type_id'] = type_id
            if self._context.get('active_id'):
                if is_reverse:
                    vals['right_partner_id'] = self._context['active_id']
                else:
                    vals['left_partner_id'] = self._context['active_id']
            if vals.get('partner_id_display'):
                if is_reverse:
                    vals['left_partner_id'] = vals['partner_id_display']
                else:
                    vals['right_partner_id'] = vals['partner_id_display']
        return vals

    @api.multi
    def _get_computed_fields(self, field_names, arg):
        """Return a dictionary of dictionaries, with for every partner for
        ids, the computed values."""
        def get_values(self, dummy_field_names, dummy_arg, context=None):
            """Get computed values for record"""
            values = {}
            on_right_partner = self.right_partner_id._on_right_partner()
            # type_selection_id
            values['type_selection_id'] = (
                ((self.type_id.id) * 10) + (on_right_partner and 1 or 0))
            # partner_id_display
            values['partner_id_display'] = (
                self.left_partner_id.id
                if on_right_partner
                else self.right_partner_id.id
            )
            # is_relation_expired
            today = fields.date.context_today(self)
            values['is_relation_expired'] = (
                self.date_end and (self.date_end < today))
            # is_relation_future
            values['is_relation_future'] = self.date_start > today
            return values

        return {i.id: get_values(i, field_names, arg) for i in self}

    @api.multi
    def write(self, vals):
        """Override write to correct values, before being stored."""
        return super(ResPartnerRelation, self).write(self._correct_vals(vals))

    @api.model
    def create(self, vals):
        """Override create to correct values, before being stored."""
        return super(ResPartnerRelation, self).create(self._correct_vals(vals))

    @api.onchange(type_selection_id)
    def on_change_type_selection_id(self):
        """Set domain on partner_id_display, when selection a relation type"""
        result = {
            'domain': {'partner_id_display': []},
            'value': {'type_id': False}
        }
        if not self.type_selection_id:
            return result
        prts_model = self.env['res.partner.relation.type.selection']
        type_model = self.env['res.partner.relation.type']
        (type_id, is_reverse) = (
            prts_model.get_type_from_selection_id(self.type_selection_id)
        )
        result['value']['type_id'] = type_id
        type_obj = type_model.browse(type_id)
        partner_domain = []
        check_contact_type = type_obj.contact_type_right
        check_partner_category = (
            type_obj.partner_category_right and
            type_obj.partner_category_right.id
        )
        if is_reverse:
            # partner_id_display is left partner
            check_contact_type = type_obj.contact_type_left
            check_partner_category = (
                type_obj.partner_category_left and
                type_obj.partner_category_left.id
            )
        if check_contact_type == 'c':
            partner_domain.append(('is_company', '=', True))
        if check_contact_type == 'p':
            partner_domain.append(('is_company', '=', False))
        if check_partner_category:
            partner_domain.append(
                ('category_id', 'child_of', check_partner_category))
        result['domain']['partner_id_display'] = partner_domain
        return result

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        """End date should not be before start date, if not filled

        :raises exceptions.Warning: When constraint is violated
        """
        if (self.date_start and self.date_end and
                self.date_start > self.date_end):
            raise exceptions.Warning(
                _('The starting date cannot be after the ending date.')
            )

    @api.one
    @api.constrains('left_partner_id', 'type_id')
    def _check_partner_type_left(self):
        """Check left partner for required company or person

        :raises exceptions.Warning: When constraint is violated
        """
        self._check_partner_type("left")

    @api.one
    @api.constrains('right_partner_id', 'type_id')
    def _check_partner_type_right(self):
        """Check right partner for required company or person

        :raises exceptions.Warning: When constraint is violated
        """
        self._check_partner_type("right")

    @api.one
    def _check_partner_type(self, side):
        """Check partner to left or right for required company or person

        :param str side: left or right
        :raises exceptions.Warning: When constraint is violated
        """
        assert side in ['left', 'right']
        ptype = getattr(self.type_id, "contact_type_%s" % side)
        company = getattr(self, '%s_partner_id' % side).is_company
        if (ptype == 'c' and not company) or (ptype == 'p' and company):
            raise exceptions.Warning(
                _('The %s partner is not applicable for this relation type.') %
                side
            )

    @api.one
    @api.constrains('left_partner_id', 'right_partner_id')
    def _check_not_with_self(self):
        """Not allowed to link partner to same partner

        :raises exceptions.Warning: When constraint is violated
        """
        if self.left_partner_id == self.right_partner_id:
            raise exceptions.Warning(
                _('Partners cannot have a relation with themselves.')
            )

    @api.one
    @api.constrains('left_partner_id', 'right_partner_id', 'active')
    def _check_relation_uniqueness(self):
        """Forbid multiple active relations of the same type between the same
        partners

        :raises exceptions.Warning: When constraint is violated
        """
        if not self.active:
            return
        domain = [
            ('type_id', '=', self.type_id.id),
            ('active', '=', True),
            ('id', '!=', self.id),
            ('left_partner_id', '=', self.left_partner_id.id),
            ('right_partner_id', '=', self.right_partner_id.id),
        ]
        if self.date_start:
            domain += ['|', ('date_end', '=', False),
                            ('date_end', '>=', self.date_start)]
        if self.date_end:
            domain += ['|', ('date_start', '=', False),
                            ('date_start', '<=', self.date_end)]
        if self.search(domain):
            raise exceptions.Warning(
                _('There is already a similar relation with overlapping dates')
            )

    @api.multi
    def get_action_related_partners(self):
        """return a window action showing a list of partners taking part in the
        relations names by ids. Context key 'partner_relations_show_side'
        determines if we show 'left' side, 'right' side or 'all' (default)
        partners.
        If active_model is res.partner.relation.all, left=this and
        right=other
        """
        if self._context.get('active_model', self._name) == self._name:
            field_names = {
                'left': ['left'],
                'right': ['right'],
                'all': ['left', 'right']
            }
        elif self._context.get('active_model') == 'res.partner.relation.all':
            field_names = {
                'left': ['this'],
                'right': ['other'],
                'all': ['this', 'other']
            }
        else:
            assert False, 'Unknown active_model!'

        partner_ids = []
        field_names = field_names[
            self._context.get('partner_relations_show_side', 'all')]
        field_names = ['%s_partner_id' % n for n in field_names]

        for relation in self.pool[self._context.get('active_model')].read(
                self._ids, load='_classic_write'):
            for name in field_names:
                partner_ids.append(relation[name])

        return {
            'name': _('Related partners'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'domain': [('id', 'in', partner_ids)],
            'views': [(False, 'tree'), (False, 'form')],
            'view_type': 'form'
        }
