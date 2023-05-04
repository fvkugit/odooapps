from odoo import models, fields, Command

class EstateProperty(models.Model):
    _inherit = "estate.property"

    def action_sold(self):
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        for reg in self:
            self.env['account.move'].create({
                "partner_id": reg.buyer_id.id,
                "move_type": "out_invoice",
                "journal_id": journal.id,
                "invoice_line_ids": [
                    Command.create({
                        "name": "Selling of " + reg.name,
                        "quantity": 1.0,
                        "price_unit": reg.selling_price * 0.06
                    }),
                    Command.create({
                        "name": "Administrative fees",
                        "quantity": 1.0,
                        "price_unit": 100.0
                    }),
                ]
            })
        # import wdb; wdb.set_trace();
        return super().action_sold()
