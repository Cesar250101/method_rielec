# -*- coding: utf-8 -*-

from ast import Try
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
import time
import logging
_logger = logging.getLogger(__name__)


class NotasCredito(models.TransientModel):
    _inherit = "pos.order.refund"

    pos_id = fields.Many2one(comodel_name='pos.config', string='POS', required=True)    
    session_id = fields.Many2one(comodel_name='pos.session', string='Session', required=True, index=True,readonly=True)
    
    @api.onchange('pos_id')
    def _onchange_(self):
        if self.pos_id:
            return {'domain':{'session_id':[('state', '=', 'opened'),('pos_id','=',self.pos_id.id)]}}

    @api.onchange('pos_id')
    def _onchange_pos_id(self):
        pos_acceso=[]
        if self.pos_id.default_partner_id:
            self.partner_id=self.pos_id.default_partner_id

        for u in self.env.user.pos_config_ids:
            pos_acceso.append(u.id)
        if self.pos_id.id not in pos_acceso and self.pos_id:
            res = {'warning': {
                        'title': _('Warning'),
                        'message': _('Usuario no esta asignado al POS %s!'%(self.pos_id.name))
                                    }
                    }
            if res:
                self.pos_id=""
                return res     
        for s in self.pos_id.session_ids:
            if s.state=='opened':
                self.session_id=s.id
                return

            res = {'warning': {
                            'title': _('Warning'),
                            'message': _('No existe una sesión abierta para el POS %s!'%(self.pos_id.name))
                                        }
                        }
            if res:
                self.session_id=""
                return res                 
    