from odoo import http
from odoo.http import request

class AbastecimentoController(http.Controller):
    @http.route('/abastecer/<int:veiculo_id>', type='http', auth='user')
    def setup_abastecimento(self, veiculo_id, **kwargs):
        # Salva o ID na sessão do usuário
        request.session['qr_veiculo_id'] = veiculo_id
        
        action = request.env.ref('controle_combustivel.action_abastecimento')
        # Redireciona para o formulário padrão
        return request.redirect(f"/odoo/action-{action.id}/new")