import urllib.parse
from odoo import models, fields, api, _, http
from odoo.http import request
from odoo.exceptions import ValidationError

class TanqueMovimento(models.Model):
    _name = 'controle.tanque.movimento'
    _description = 'Histórico de Movimentação de Combustível'
    _order = 'data desc'

    tanque_id = fields.Many2one('controle.tanque', string="Tanque", required=True, ondelete='cascade')
    data = fields.Datetime(string="Data/Hora", default=fields.Datetime.now, readonly=True)
    tipo = fields.Selection([
        ('entrada', 'Entrada (Carga)'),
        ('saida', 'Saída (Abastecimento)')
    ], string="Tipo", required=True, readonly=True)
    
    quantidade = fields.Float(string="Quantidade (L)", required=True, readonly=True)
    
    # Campos de Referência para saber de onde veio o movimento
    origem = fields.Char(string="Origem/Documento", readonly=True) 
    usuario_id = fields.Many2one('res.users', string="Responsável", default=lambda self: self.env.user, readonly=True)

class TanqueCombustivel(models.Model):
    _name = 'controle.tanque'
    _description = 'Controle de Tanque'

    name = fields.Char(string="Tanque", default="Principal (6.000L)", required=True)
    capacidade_max = fields.Float(string="Capacidade Máxima", default=6000.0)
    valor_litro = fields.Float(string="Preço por Litro (R$)", default=0.0)
    
    movimento_ids = fields.One2many('controle.tanque.movimento', 'tanque_id', string="Movimentações")

    estoque_atual = fields.Float(
        string="Estoque Atual", 
        compute="_compute_estoque", 
        store=True,
        help="Saldo calculado automaticamente através do histórico de entradas e saídas."
    )

    # Função que soma as entrada e subtrai as saídas
    @api.depends('movimento_ids.quantidade', 'movimento_ids.tipo')
    def _compute_estoque(self):
        for tanque in self:
            # Filtra e soma entradas
            entradas = sum(tanque.movimento_ids.filtered(lambda m: m.tipo == 'entrada').mapped('quantidade'))
            # Filtra e soma saídas
            saidas = sum(tanque.movimento_ids.filtered(lambda m: m.tipo == 'saida').mapped('quantidade'))
            # Define o saldo final
            tanque.estoque_atual = entradas - saidas

    def action_entrada_combustivel(self):
        return {
            'name': 'Recarregar Tanque (Entrada de Diesel)',
            'type': 'ir.actions.act_window',
            'res_model': 'controle.tanque.entrada.wizard',
            'view_mode': 'form',
            'target': 'new',
            }
    
    @api.constrains('estoque_atual', 'capacidade_max')
    def _check_capacidade_limite(self):
        for record in self:
            if record.estoque_atual > record.capacidade_max:
                raise ValidationError(
                    _("Operação cancelada! O estoque atual (%.2f L) não pode exceder a capacidade máxima do tanque (%.2f L).") 
                    % (record.estoque_atual, record.capacidade_max)
                )

class TanqueEntradaWizard(models.TransientModel):
    _name = 'controle.tanque.entrada.wizard'
    _description = 'Wizard de Entrada de Combustível'

    quantidade_entrada = fields.Float(string="Quantidade a Adicionar (L)", required=True)

    def action_confirmar_entrada(self):
        tanque_id = self.env.context.get('active_id')
        if not tanque_id:
            return

        tanque_real = self.env['controle.tanque'].browse(tanque_id)

        # Validação de espaço
        espaco_vazio = tanque_real.capacidade_max - tanque_real.estoque_atual
        if self.quantidade_entrada > espaco_vazio:
            raise ValidationError(
                _("Capacidade excedida! O tanque suporta apenas mais %.2f L.") % espaco_vazio
            )

        # Criação do histórico
        self.env['controle.tanque.movimento'].create({
            'tanque_id': tanque_real.id,
            'tipo': 'entrada',
            'quantidade': self.quantidade_entrada,
            'origem': "Carga de Diesel (Entrada Manual)",
        })
        
        return {'type': 'ir.actions.act_window_close'}
    
class ControleCaminhao(models.Model):
    _name = 'controle.caminhao'
    _description = 'Frota de Veículos'
    _rec_name = 'display_name'

    name = fields.Char(string="Identificação", required=True)
    placa = fields.Char(string="Placa/Série", required=True)
    disponivel = fields.Boolean(string="Disponível para Uso", default=True)
    qr_link = fields.Char(string="Link do QR Code", compute="_compute_qr_link")

    display_name = fields.Char(compute='_compute_display_name', store=True)

    tipo_veiculo = fields.Selection([
        ('caminhao', 'Caminhão'),
        ('empilhadeira', 'Empilhadeira')
    ], string="Tipo de Veículo", default='caminhao', required=True)

    odometro_inicial = fields.Float(string="Odômetro Atual (KM)")
    horimetro_inicial = fields.Float(string="Horímetro Atual (h)")
    capacidade_tanque = fields.Float(string="Capacidade do Tanque (L)")
    
    def _compute_qr_link(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            record.qr_link = f"{base_url}/abastecer/{record.id}"

    @api.depends('name', 'placa')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} ({record.placa})" if record.name and record.placa else record.name

class ControleAbastecimento(models.Model):
    _name = 'controle.combustivel.abastecimento'
    _description = 'Registros de Abastecimento'
    
    valor_litro = fields.Float(string="Valor por Litro", readonly=True, store=True)

    @api.onchange('tanque_id')
    def _onchange_tanque_id(self):
        if self.tanque_id:
            self.valor_litro = self.tanque_id.valor_litro
    

    @api.model
    def _get_default_tanque(self):
        tanque = self.env['controle.tanque'].search([], limit=1)
        return tanque.id if tanque else False

    @api.model
    def default_get(self, fields_list):
        res = super(ControleAbastecimento, self).default_get(fields_list)
        
        if request and request.session.get('qr_veiculo_id'):
            qr_id = request.session.get('qr_veiculo_id')
            res.update({'caminhao_id': int(qr_id)})
            
            # Limpa para o próximo não vir preenchido errado
            request.session.pop('qr_veiculo_id', None)
            
        return res
    
    tanque_id = fields.Many2one('controle.tanque', string="Tanque", required=True, default=lambda self: self.env['controle.tanque'].search([], limit=1).id)
    
    caminhao_id = fields.Many2one(
        'controle.caminhao', 
        string="Veículo", 
        required=True, 
        domain=[('disponivel', '=', True)]
    )
    
    motorista_id = fields.Many2one('res.users', string="Motorista", default=lambda self: self.env.user)
    quantidade_litros = fields.Float(string="Litros Abastecidos", required=True)
    data_abastecimento = fields.Datetime(string="Data e Hora", default=fields.Datetime.now)
    
    state = fields.Selection([
        ('done', 'Confirmado'),
        ('cancel', 'Estornado')
    ], string="Status", default='done', readonly=True, copy=False)

    odometro = fields.Float(string="Odômetro (KM)")
    horimetro = fields.Float(string="Horímetro (h)")
    
    tipo_veiculo = fields.Selection(related='caminhao_id.tipo_veiculo', string="Tipo", store=True)
    placa_veiculo = fields.Char(related='caminhao_id.placa', string="Placa/Série", readonly=True)
    ultimo_odometro = fields.Float(string="Último Odômetro Registrado", readonly=True)
    ultimo_horimetro = fields.Float(string="Último Horímetro Registrado", readonly=True)

    valor_total = fields.Float(string="Total", compute="_compute_total", store=True)

    @api.onchange('caminhao_id')
    def _onchange_caminhao_id(self):
        if self.caminhao_id:
            self.ultimo_odometro = self.caminhao_id.odometro_inicial
            self.ultimo_horimetro = self.caminhao_id.horimetro_inicial
        else:
            self.ultimo_odometro = 0.0
            self.ultimo_horimetro = 0.0

    # Trava de Segurança: Impede KM/Hora menor que a anterior
    @api.constrains('odometro', 'horimetro', 'caminhao_id')
    def _check_medicao_progressiva(self):
        for record in self:
            if record.tipo_veiculo == 'caminhao':
                if record.odometro < record.caminhao_id.odometro_inicial:
                    raise ValidationError(_(
                        "Erro no Odômetro! O valor atual (%.2f KM) não pode ser menor que o último registro (%.2f KM)."
                    ) % (record.odometro, record.caminhao_id.odometro_inicial))
            
            if record.tipo_veiculo == 'empilhadeira':
                if record.horimetro < record.caminhao_id.horimetro_inicial:
                    raise ValidationError(_(
                        "Erro no Horímetro! O valor atual (%.2f h) não pode ser menor que o último registro (%.2f h)."
                    ) % (record.horimetro, record.caminhao_id.horimetro_inicial))

    @api.depends('quantidade_litros', 'valor_litro')
    def _compute_total(self):
        for record in self:
            record.valor_total = record.quantidade_litros * record.valor_litro

    @api.model_create_multi
    def create(self, vals_list):
        # 1. Validações Prévias (Disponibilidade e Estoque)
        for vals in vals_list:
            veiculo = self.env['controle.caminhao'].browse(vals.get('caminhao_id')).sudo()
            tanque = self.env['controle.tanque'].browse(vals.get('tanque_id') or self._get_default_tanque()).sudo()

            if not veiculo.disponivel:
                raise ValidationError(_("Operação Cancelada: O veículo %s está marcado como INDISPONÍVEL no sistema.") % veiculo.display_name)

            if tanque.estoque_atual < vals.get('quantidade_litros', 0.0):
                raise ValidationError(_("Estoque insuficiente no tanque %s!") % tanque.name)

        # 2. Criação dos registros (Dispara as constraints de validação de odômetro/horímetro)
        records = super().create(vals_list)

        # 3. Atualização do Veículo e Movimentação do Tanque (Pós-criação)
        for record in records:
            veiculo = record.caminhao_id.sudo()
            tanque = record.tanque_id.sudo()

            if veiculo.tipo_veiculo == 'empilhadeira':
                veiculo.horimetro_inicial = record.horimetro
            else:
                veiculo.odometro_inicial = record.odometro

            self.env['controle.tanque.movimento'].sudo().create({
                'tanque_id': tanque.id,
                'tipo': 'saida',
                'quantidade': record.quantidade_litros,
                'origem': f"Abastecimento: {veiculo.display_name}",
            })
        return records
    
    def action_estorno(self):
        """ Reverte o abastecimento: devolve combustível ao tanque e tenta resetar KM/H do veículo """
        for record in self:
            if record.state == 'cancel':
                raise ValidationError(_("Este abastecimento já foi estornado."))

            # 1. Devolver o combustível ao tanque (Movimento de Entrada)
            self.env['controle.tanque.movimento'].sudo().create({
                'tanque_id': record.tanque_id.id,
                'tipo': 'entrada',
                'quantidade': record.quantidade_litros,
                'origem': _("ESTORNO: Abastecimento de %s") % record.caminhao_id.display_name,
            })

            # 2. Reverter Odômetro/Horímetro no cadastro do veículo
            # Só revertemos se o valor atual do veículo for exatamente o que este registro gravou
            # (evita bagunçar o KM se já houverem abastecimentos posteriores)
            veiculo = record.caminhao_id.sudo()
            if record.tipo_veiculo == 'caminhao':
                if veiculo.odometro_inicial == record.odometro:
                    veiculo.odometro_inicial = record.ultimo_odometro
            elif record.tipo_veiculo == 'empilhadeira':
                if veiculo.horimetro_inicial == record.horimetro:
                    veiculo.horimetro_inicial = record.ultimo_horimetro

            # 3. Atualizar status do registro
            record.write({'state': 'cancel'})
            
        return True