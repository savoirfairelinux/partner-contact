# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.osv import expression


class ResPartnerGroup(models.Model):

    _name = 'res.partner.group'

    rule_ids = fields.One2many('res.partner.rule', 'partner_group_id', 'Rules')
    domain = fields.Text()

    @api.multi
    def apply_rules(self, partner_ids, operation):
        self.ensure_one()
        groups = self.env.user.groups_id
        rule_domains = []

        for rule in self.rule_ids:
            if rule.group_id not in groups:
                continue

            if operation == 'read':
                if not rule.erpread:
                    continue

            elif operation == 'write':
                if not operation.erpwrite:
                    continue

            elif operation == 'create':
                if not operation.erpcreate:
                    continue

            elif operation == 'unlink':
                if not operation.erpunlink:
                    continue

            rule_domains.append(expression.normalize_domain(rule.domain))

        if not rule_domains:
            return set()

        domain = expression.OR(map(expression.OR, rule_domains.values()))
        domain = expression.AND([domain, ('id', 'in', partner_ids)])
        return set(self.with_context(active_test=False).search(domain).ids)
