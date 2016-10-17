# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, SUPERUSER_ID
from openerp.osv import expression


class ResPartnerRule(models.Model):

    _name = 'res.partner.rule'

    partner_group_id = fields.Many2one(
        'res.partner.group', 'Group', required=True, ondelete='cascade')

    group_id = fields.Many2one(
        'res.groups', 'Group', required=True, ondelete='cascade')

    read = fields.Boolean('Read')
    write = fields.Boolean('Write')
    create = fields.Boolean('Create')
    unlink = fields.Boolean('Delete')

    domain = fields.Text()

    @api.multi
    def apply_rules(self, partner_ids, operation):
        self.ensure_one()

        rules_to_apply = self.sudo().rule_ids.browse([
            (operation, '=', True),
            ('group_id', 'in', self.env.user.groups_id.ids)
        ])

        rule_domains = []
        for rule in rules_to_apply:
            rule_domains.append(expression.normalize_domain(rule.domain))

        if not rule_domains:
            return set()

        domain = expression.AND([
            ('id', 'in', partner_ids),
            expression.OR(rule_domains),
        ])
        return set(self.with_context(active_test=False).search(domain).ids)

    @api.model
    def compute_domain(self, mode):
        if self.env.user.id == SUPERUSER_ID:
            return None

        rules = self.sudo().search([
            ('group_id.users', '=', self.env.user.id), (mode, '=', True)
        ])

        rule_domains = [('partner_group_id', '=', False)]

        for rule in rules:
            rule_domains.append(expression.AND([
                ('partner_group_id', '=', rule.partner_group_id.id),
                expression.normalize_domain(rule.domain),
            ]))

        return expression.OR(rule_domains)
