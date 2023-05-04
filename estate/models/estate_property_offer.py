from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare

class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "estate.property.offer"
    _order = "price desc"

    price = fields.Float("Price", required=True)
    status = fields.Selection(string="Status", selection=[("accepted","Accepted"), ("refused", "Refused"), ("pending", "Pending")], default="pending", copy=False)
    validity = fields.Integer("Validity", default=7)
    partner_id = fields.Many2one("res.partner", "Buyer", required=True)
    property_id = fields.Many2one("estate.property", "Property", required=True)

    property_type_id = fields.Many2one("estate.property.type", related="property_id.property_type_id", string="Property type", store=True)

    # COMPUTED FIELDS  #
    date_deadline = fields.Date("Date deadline", compute="_compute_date_deadline", inverse="_inverse_date_deadline")
    @api.depends("validity", "create_date")
    def _compute_date_deadline(self):
        for r in self:
            base_date = r.create_date.date() if r.create_date else fields.Date.today()
            r.date_deadline = base_date + relativedelta(days=r.validity)

    def _inverse_date_deadline(self):
        for r in self:
            base_date = r.create_date.date() if r.create_date else fields.Date.today()
            r.validity = (r.date_deadline - base_date).days

    # ACTIONS #
    def action_accept(self):
        if "accepted" in self.mapped("property_id.offer_ids.status"):
            raise UserError("An offer as already been accepted.")
        self.write({"status": "accepted"})
        self.mapped("property_id").write({
            "state": "accepted",
            "selling_price": self.price,
            "buyer_id": self.partner_id.id
        })
    def action_refuse(self):
        self.write({"status": "refused"})

    _sql_constraints = [
        ("check_price", "CHECK(price>0)", "An offer price must be strictly positive")
    ]

    # OVERRIDE METHODS #
    @api.model
    def create(self, values):
        if (values.get("property_id") and values.get("price")):
            prop_id = values["property_id"]
            prop = self.env['estate.property'].browse(prop_id)
            if (prop.offer_ids):
                max_offer = max(prop.mapped("offer_ids.price"))
                if (float_compare(values["price"], max_offer, precision_rounding=0.01) <= 0):
                    raise UserError("The offer price must be higher than %.2f" % max_offer)
            prop.state = "received"
        return super().create(values)
