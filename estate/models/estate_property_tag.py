from odoo import models, fields, api

class EstatePropertyTag(models.Model):
    _name = "estate.property.tag"
    _description = "estate.property.tag"
    _order = "name"

    name = fields.Char("Tag", required=True)
    color = fields.Integer("Color")

    _sql_constraints = [
    ("name_unique", "unique (name)", "Tag name already exists"),
    ]
