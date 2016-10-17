==============
Partner Access
==============
In vanilla Odoo, any user can access any partner. In some cases, it is a security issue.

For example, if you enter the personal addresses of your employees, the whole company
will be able to see it.

In sales, you might only want a user to access the customers related to his own leads.

Because the access to a partner depends on the context of the partner, standard record rules
are not well adapted.

This modules aims to restrict partner access with a maximum of flexibility while minimizing
the overhead of record rules.

How it works
------------
Each partner can be restricted or not. This is done by the new field access_level.

If a partner is restricted, it must be linked to a special record rule.
Each rule may contain a domain filter, a group, or both.

When searching partners, the standard search methods are applied.
Then, all records found are grouped by special rule.
Each special rule is computed one time and then records related to the succeeding
rules are returned as a result.

When reading, the same strategy is applied.

The difference with a standard record rule (ir.rule) is that each special rule
is not computed at every request, but only when a partner related to the rule is found.

It is more flexible because it allows partners to be managed separately for each use case.
For example, you could restrict suppliers to a group of users and customers to another.
