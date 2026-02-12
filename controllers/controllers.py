# from odoo import http


# class ControleCombustivel(http.Controller):
#     @http.route('/controle_combustivel/controle_combustivel', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/controle_combustivel/controle_combustivel/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('controle_combustivel.listing', {
#             'root': '/controle_combustivel/controle_combustivel',
#             'objects': http.request.env['controle_combustivel.controle_combustivel'].search([]),
#         })

#     @http.route('/controle_combustivel/controle_combustivel/objects/<model("controle_combustivel.controle_combustivel"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('controle_combustivel.object', {
#             'object': obj
#         })

