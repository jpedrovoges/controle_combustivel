/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onWillStart } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup();
        onWillStart(async () => {
            // Verifica se estamos no modelo de abastecimento e se é um registro novo
            if (this.props.resModel === "controle.combustivel.abastecimento" && !this.props.resId) {
                const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || window.location.search);
                const veiculoId = urlParams.get('default_caminhao_id');
                
                if (veiculoId) {
                    // Força o preenchimento do campo no contexto da view
                    this.props.context.default_caminhao_id = parseInt(veiculoId);
                }
            }
        });
    },
});