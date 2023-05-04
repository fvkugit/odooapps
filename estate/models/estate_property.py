import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'estate.property'
    _order = "id desc"

    name = fields.Char("Property name", required=True)
    description = fields.Text("Property description")
    postcode = fields.Char("Postcode")
    date_availability = fields.Date("Date availability", copy=False, default=lambda self: fields.Date.add(fields.Date.today(), months=3))
    expected_price = fields.Float("Expected price", required=True)
    selling_price = fields.Float("Selling price", readonly=True, copy=False)
    bedrooms = fields.Integer("Bedrooms", default=2)
    living_area = fields.Integer("Living area")
    facades = fields.Integer("Facades")
    garage = fields.Boolean("Garage")
    garage_area = fields.Integer("Garage area")
    garden = fields.Boolean("Garden")
    garden_area = fields.Integer("Garden area")
    active = fields.Boolean("Active", default=True)
    state = fields.Selection(string="Property State", required=True, copy=False, default="new", selection=[
                                              ('new', "New"),
                                              ('received', "Offer Received"),
                                              ('accepted', "Offer Accepted"),
                                              ('sold', "Sold"),
                                              ('canceled', "Canceled")
                                          ])
    garden_orientation = fields.Selection(string="Type",
                                          selection=[
                                            ('n', "North"),
                                            ('s', "South"),
                                            ('e', "East"),
                                            ('w', "West")
                                          ],
                                          help="Select garen orientation")

    # RELATIONS #
    property_type_id = fields.Many2one("estate.property.type", string="Property type")
    user_id = fields.Many2one("res.users", string="Salesman", default=lambda self: self.env.user)
    buyer_id = fields.Many2one("res.partner", string="Buyer", copy=False)
    tag_ids = fields.Many2many("estate.property.tag", string="Tags")
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")

    # COMPUTED FIELDS #
    total_area = fields.Integer(compute="_compute_total_area")
    @api.depends("living_area", "garden_area")
    def _compute_total_area(self):
        for r in self:
            r.total_area = (r.living_area + r.garden_area)

    best_offer = fields.Float(compute="_compute_best_offer")
    @api.depends("offer_ids")
    def _compute_best_offer(self):
        for r in self:
            r.best_offer = max(r.offer_ids.mapped("price")) if r.offer_ids else 0

    # ONCHANGE #
    @api.onchange("garden")
    def _onchange_garden(self):
        for r in self:
            r.garden_area = 10 if self.garden else 0
            r.garden_orientation = "n" if self.garden else False

    # ACTIONS #
    def action_sold(self):
        if "canceled" in self.mapped("state"):
            raise UserError("Can't sold a canceled property.")
        self.write({"state": "sold"})
    def action_cancel(self):
        if "sold" in self.mapped("state"):
            raise UserError("Can't cancel a sold property.")
        self.write({"state": "canceled"})

    # CONSTRAINTS #
    _sql_constraints = [
        ("check_expected_price", "CHECK(expected_price>0)", "A property expected price must be strictly positive"),
        ("check_selling_price", "CHECK(selling_price>=0)", "A property selling price must be positive"),
    ]

    @api.constrains("selling_price", "expected_price")
    def _check_selling_price(self):
        for r in self:
            if (not float_is_zero(r.selling_price, precision_rounding=0.01) and float_compare(r.selling_price, r.expected_price * 0.9, precision_rounding=0.01) < 0):
                raise ValidationError("Selling price cannot be lower than 90% of the expected price.")


    # OVERRIDE METHODS #
    def unlink(self):
        if not set(self.mapped("state")) <= {"new", "canceled"}:
            raise UserError("Can't delete a property with new or canceled state.")
        return super().unlink()
