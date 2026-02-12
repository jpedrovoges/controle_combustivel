# Controle de Combustível - Odoo 19

Módulo para gestão de frota interna, controle de estoque de tanques e registro de abastecimentos com travas de segurança.

##  Requisitos de Instalação
Este módulo foi desenvolvido para ser **plug-and-play**. 

- **Odoo:** Versão 19.0
- **Python:** 3.12+ (sem bibliotecas externas necessárias)

##  Como Instalar
1. Copie a pasta `controle_combustivel` para o diretório de addons do seu Odoo.
2. Adicione o caminho da pasta no seu arquivo `odoo.conf` no parâmetro `addons_path`.
3. Reinicie o servidor Odoo.
4. No modo desenvolvedor, vá em **Aplicações > Atualizar Lista de Módulos**.
5. Procure por "Controle de Combustível" e clique em **Instalar**.

##  Segurança Implementada
- **Motoristas:** Só visualizam a tela de registro; não podem alterar data/hora, trocar o nome do responsável ou excluir registros.
- **Gerentes:** Acesso total à gestão de tanques, frota e parâmetros técnicos.
- **Validação:** O sistema impede a inserção de quilometragem menor que a última registrada no caminhão.