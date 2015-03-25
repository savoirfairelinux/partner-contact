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
    any_partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        compute='_get_any_partner_id',
    )
    type_id = fields.Many2one(
        'res.partner.relation.type',
        string='Type',
        required=True,
        auto_join=True,
    )
    date_start = fields.Date('Starting date')
    date_end = fields.Date('Ending date')
    active = fields.Boolean('Active', default=True)

    @api.one
    @api.depends("left_partner_id", "right_partner_id")
    def _get_any_partner_id(self):
        """Get any relationship whether the partner is on the right or left
        """
        self.any_partner_id = self.left_partner_id + self.right_partner_id

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
