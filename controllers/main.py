from odoo import http
from odoo.http import request

class FuelQRController(http.Controller):
    @http.route('/fill/fuel', type='http', auth="user")
    def redirect_fuel_form(self, placa=None, **kwargs):
        # 1. Busca o caminhão pela placa
        caminhao = request.env['controle.caminhao'].sudo().search([('placa', '=', placa)], limit=1)
        
        if not caminhao:
            return "Erro: Caminhão com a placa %s não encontrado." % placa

        # 2. Em vez de montar a URL na mão com #, vamos montar os parâmetros de busca
        # Isso força o Odoo a reconhecer o contexto de 'default_'
        model = 'controle.combustivel.abastecimento'
        action = request.env.ref('controle_combustivel.action_abastecimento')
        
        # Construindo a URL de forma que o Odoo Web Client processe o Contexto
        redirect_url = (
            f"/web#action={action.id}"
            f"&model={model}"
            f"&view_type=form"
            f"&additional_context={{'default_caminhao_id': {caminhao.id}}}"
        )
        
        return request.redirect(redirect_url)