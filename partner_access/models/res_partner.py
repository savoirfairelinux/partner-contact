# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from openerp import api, fields, models, _, SUPERUSER_ID
from openerp.exceptions import AccessError


class ResPartner(models.Model):

    _inherit = 'res.partner'

    partner_group_id = fields.Many2one('res.partner.group', 'Group')
    domain = fields.Text()

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).write(vals)
        res.propagate_partner_group()
        return res

    @api.multi
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if 'parent_id' in vals or 'partner_group_id' in vals:
            self.propagate_partner_group()
        return res

    @api.multi
    def propagate_partner_group(self):
        for partner in self:
            if (
                partner.parent_id and
                partner.partner_group_id != partner.parent_id.partner_group_id
            ):
                partner.partner_group_id = partner.parent_id.partner_group_id
            elif partner.is_company:
                children_to_update = partner.child_ids.filtered(
                    lambda c: c.partner_group_id != partner.partner_group_id)
                children_to_update.write({
                    'partner_group_id': partner.partner_group_id.id
                })

    @api.multi
    def check_access_rule(self, operation):
        res = super(ResPartner, self).check_access_rule(operation)

        if not self.ids:
            return res

        self.env.cr.execute(
            """
            SELECT id, partner_group_id FROM res_partner
            WHERE id IN %s AND partner_group_id IS NOT NULL
            """, (tuple(self.ids), )
        )

        partners_by_group = defaultdict(list)

        for partner_id, group_id in self.env.cr.fetchall():
            partners_by_group[group_id].append(partner_id)

        groups = self.env['res.partner.group'].sudo().browse(
            partners_by_group.keys())

        for group in groups:
            partner_ids = partners_by_group[group.id]
            allowed_partner_ids = group.apply_rules(partner_ids, operation)

            if set(partner_ids) - allowed_partner_ids:
                raise AccessError(
                    _('For this kind of document, you may only '
                      'access records you created yourself.'
                      '\n\n(Document type: %s)') % (self._description,))
        return res

    @api.model
    def _apply_ir_rules(self, query, mode='read'):
        super(ResPartner, self)._apply_ir_rules(query, mode=mode)
        if self.env.user.id == SUPERUSER_ID:
            return

        domain = self.env['res.partner.rule'].compute_domain(mode)

        if domain:
            rule_query = self.sudo()._where_calc(domain, active_test=False)
            query.where_clause += rule_query.added_clause
            query.where_clause_params += rule_query.added_params
            for table in rule_query.added_tables:
                if table not in query.tables:
                    query.tables.append(table)
