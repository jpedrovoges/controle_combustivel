from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ControleCaminhao(models.Model):
    _name = 'controle.caminhao'
    _description = 'Cadastro de Caminhões'

    name = fields.Char(string="Nome do Caminhão", required=True)
    placa = fields.Char(string="Placa", required=True)
    odometro_inicial = fields.Float(string="Odômetro Atual", help="Kilometragem atual do veículo")
    capacidade_tanque = fields.Float(string="Capacidade do Tanque (L)")

class Abastecimento(models.Model):
    _name = 'controle.abastecimento'
    _description = 'Registro de Abastecimento'

    caminhao_id = fields.Many2one('controle.caminhao', string="Caminhão", required=True)
    odometro_anterior = fields.Float(
        related='caminhao_id.odometro_inicial', 
        string="Último Odômetro Registrado", 
        readonly=True
    )
    placa_veiculo = fields.Char(related='caminhao_id.placa', string="Placa", readonly=True, store=True)
    motorista_id = fields.Many2one('res.users', string="Motorista", default=lambda self: self.env.user)
    data_abastecimento = fields.Datetime(string="Data e Hora", default=fields.Datetime.now)
    odometro = fields.Float(string="Odômetro")
    quantidade_litros = fields.Float(string="Litros Abastecidos", required=True)
    valor_litro = fields.Float(string="Valor por Litro")
    valor_total = fields.Float(string="Total", compute="_compute_total", store=True)

    @api.depends('quantidade_litros', 'valor_litro')
    def _compute_total(self):
        for record in self:
            record.valor_total = record.quantidade_litros * record.valor_litro

    def write(self, vals):
        """ Impede a alteração da data/hora após o registro ser criado """
        if 'data_abastecimento' in vals:
            raise ValidationError("Não é permitido alterar a data/hora de um abastecimento já registrado.")
        return super(Abastecimento, self).write(vals)

    def unlink(self):
        """ Impede a exclusão por quem não é Gerente """
        for record in self:
            if not self.env.user.has_group('controle_combustivel.group_combustivel_manager'):
                raise ValidationError("Motoristas não têm permissão para excluir registros de abastecimento.")
        return super(Abastecimento, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        tanque_model = self.env['controle.tanque'].sudo()
        for vals in vals_list:
            # 1. Trava de Segurança do Motorista
            if not self.env.user.has_group('controle_combustivel.group_combustivel_manager'):
                vals['motorista_id'] = self.env.uid

            # 2. Validação do Odômetro (Não pode ser menor que o atual)
            if vals.get('caminhao_id') and vals.get('odometro'):
                caminhao = self.env['controle.caminhao'].sudo().browse(vals['caminhao_id'])
                
                if vals['odometro'] < caminhao.odometro_inicial:
                    raise ValidationError(
                        f"Erro no Odômetro! O último registro deste caminhão foi {caminhao.odometro_inicial}. "
                        f"Você não pode inserir um valor menor ({vals['odometro']})."
                    )
                
                # Se passou na validação, atualiza o odômetro do caminhão para o novo valor
                caminhao.odometro_inicial = vals['odometro']

            # 3. Baixa no Estoque do Tanque
            tanque = tanque_model.search([], limit=1)
            if tanque:
                litros = vals.get('quantidade_litros', 0)
                if tanque.estoque_atual < litros:
                    raise ValidationError(f"Estoque insuficiente! Disponível: {tanque.estoque_atual}L.")
                tanque.estoque_atual -= litros
                
        return super(Abastecimento, self).create(vals_list)

class TanqueCombustivel(models.Model):
    _name = 'controle.tanque'
    _description = 'Controle de Tanque'

    name = fields.Char(string="Tanque", default="Principal (6.000L)")
    capacidade_max = fields.Float(string="Capacidade Máxima", default=6000.0)
    estoque_atual = fields.Float(string="Estoque Atual", default=6000.0)

    def action_entrada_combustivel(self):
        return {
            'name': 'Entrada de Combustível',
            'type': 'ir.actions.act_window',
            'res_model': 'controle.tanque.entrada.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

class TanqueEntradaWizard(models.TransientModel):
    _name = 'controle.tanque.entrada.wizard'
    _description = 'Wizard de Entrada'

    quantidade_entrada = fields.Float(string="Quantidade a Adicionar (L)", required=True)

    def action_confirmar_entrada(self):
        tanque_id = self.env.context.get('active_id')
        tanque = self.env['controle.tanque'].browse(tanque_id)
        if tanque:
            tanque.estoque_atual += self.quantidade_entrada