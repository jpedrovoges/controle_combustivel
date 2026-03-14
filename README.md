# Controle de Combustível (Odoo 19)

Módulo desenvolvido para **gestão de abastecimento de frota interna e controle de estoque de combustível em tanques**, com foco em **integridade de dados, rastreabilidade de operações e prevenção de erros operacionais**.

O sistema permite registrar abastecimentos de caminhões e empilhadeiras, controlar o saldo do tanque principal, manter histórico completo de movimentações e aplicar regras automáticas de validação para garantir consistência nos dados de operação da frota.

---

# 📋 Pré-requisitos de Funcionamento

Para que o módulo opere corretamente após a instalação, é necessário configurar alguns dados básicos do sistema.

### Cadastro da Frota

Todos os veículos ou equipamentos devem possuir:

* Identificação do veículo
* Placa ou número de série
* Tipo de veículo (Caminhão ou Empilhadeira)
* Medição inicial:

  * **Odômetro inicial (KM)** para caminhões
  * **Horímetro inicial (Horas)** para empilhadeiras
* Capacidade do tanque do veículo (opcional, para referência operacional)

### Cadastro do Tanque

Deve existir **pelo menos um tanque de combustível cadastrado** no sistema.

O tanque deve possuir:

* Nome ou identificação
* Capacidade máxima
* Estoque inicial de combustível (registrado através de movimentação de entrada)

### Usuários e Permissões

Os usuários do sistema devem ser vinculados a um dos grupos de segurança:

* **Motorista**
* **Analista**
* **Administrador do Módulo**

Esses grupos controlam o nível de acesso e as permissões dentro do sistema.

---

# ⚙️ Requisitos Técnicos

* **Odoo:** Versão 19.0 (Community ou Enterprise)
* **Python:** 3.12 ou superior
* **Dependências Odoo:**

  * `base`

O módulo foi desenvolvido de forma independente, sem dependências de módulos de frota ou estoque nativos do Odoo.

---

# 🚀 Instalação Rápida

1. Copie a pasta do módulo:

```
controle_combustivel
```

para o diretório de addons do seu ambiente Odoo.

2. Verifique se o caminho está configurado no arquivo:

```
odoo.conf
```

exemplo:

```
addons_path = /odoo/addons,/odoo/custom_addons
```

3. Reinicie o serviço do Odoo.

4. Ative o **Modo Desenvolvedor** no Odoo.

5. Vá até:

```
Aplicações → Atualizar Lista de Aplicações
```

6. Procure pelo módulo:

```
Controle de Combustível
```

7. Clique em **Instalar**.

---

# 🚛 Estrutura Funcional do Sistema

O módulo é composto por quatro componentes principais:

### Frota de Veículos

Cadastro dos veículos e equipamentos que podem ser abastecidos.

Campos principais:

* Identificação do veículo
* Placa ou número de série
* Tipo de veículo
* Odômetro ou horímetro atual
* Disponibilidade para uso

O sistema mantém automaticamente a **última medição registrada** para evitar regressões nos valores.

---

### Tanques de Combustível

Gerencia os tanques internos da empresa.

Cada tanque possui:

* Capacidade máxima
* Estoque atual calculado automaticamente
* Histórico completo de entradas e saídas

O estoque **não é editado manualmente**, sendo calculado com base nas movimentações registradas.

---

### Movimentações de Estoque

Toda entrada ou saída de combustível gera automaticamente um registro de movimentação.

Tipos de movimentação:

* **Entrada:** carga de combustível no tanque
* **Saída:** abastecimento realizado em veículo

Cada movimentação registra:

* Data e hora
* Quantidade
* Origem da operação
* Usuário responsável

Isso cria um **extrato completo de auditoria do tanque**.

---

### Registros de Abastecimento

Cada abastecimento gera um registro contendo:

* Veículo abastecido
* Motorista responsável
* Litros abastecidos
* Valor por litro
* Valor total
* Medição atual (KM ou Horas)
* Data e hora do abastecimento
* Tanque utilizado

Após a confirmação, o sistema:

1. Atualiza o **odômetro ou horímetro do veículo**
2. Gera uma **movimentação de saída no tanque**
3. Atualiza automaticamente o **saldo do tanque**

---

# 🔐 Camadas de Segurança e Permissões

O módulo implementa controle de acesso baseado em grupos de usuários.

## Motorista

Permissões:

* Registrar abastecimentos
* Visualizar apenas **seus próprios registros**
* Consultar veículos
* Consultar saldo de tanques

Restrições:

* Não pode excluir registros
* Não pode alterar configurações
* Não pode manipular estoque manualmente

---

## Analista

Permissões:

* Registrar e visualizar todos os abastecimentos
* Gerenciar cadastro de veículos
* Gerenciar tanques
* Registrar entrada de combustível no tanque
* Consultar movimentações de estoque

Restrições:

* Não possui permissões administrativas completas

---

## Administrador do Módulo

Permissões completas sobre o sistema:

* Gerenciar usuários
* Alterar configurações
* Editar registros
* Estornar abastecimentos
* Gerenciar toda a estrutura do módulo

---

# 🔒 Camadas de Validação e Integridade de Dados

O sistema implementa diversas regras automáticas para evitar inconsistências operacionais.

### Validação de Odômetro e Horímetro

O sistema garante que a nova medição seja sempre maior que a anterior.

Regra aplicada:

```
Valor atual > Última medição registrada
```

Caso contrário, o sistema bloqueia o registro do abastecimento.

---

### Controle de Estoque do Tanque

Antes de confirmar um abastecimento, o sistema verifica se existe combustível suficiente no tanque.

Se a quantidade solicitada for maior que o saldo disponível, o registro é bloqueado.

---

### Controle de Capacidade do Tanque

Ao registrar entradas de combustível no tanque, o sistema impede que o estoque ultrapasse a capacidade máxima definida.

---

### Estorno de Abastecimento

Abastecimentos podem ser estornados por usuários autorizados.

Ao estornar um abastecimento:

1. O combustível retorna automaticamente ao tanque.
2. O sistema tenta restaurar a medição anterior do veículo (quando aplicável).
3. O registro é marcado como **cancelado**, preservando o histórico.

---

# 📊 Auditoria e Rastreabilidade

Todas as operações importantes do sistema são registradas automaticamente:

* Movimentações de combustível
* Usuário responsável
* Data e hora da operação
* Origem da movimentação

Isso garante **total rastreabilidade das operações de abastecimento e controle de estoque**.

---

# 📌 Observações Operacionais

* O sistema assume a existência de **um tanque principal** por padrão.
* O controle de estoque é **totalmente baseado em movimentações**, não sendo possível alterar o saldo diretamente.
* Registros confirmados **não podem ser excluídos**, apenas estornados.
* O módulo foi projetado para uso em **ambientes industriais, transportadoras e operações logísticas internas**.

---

# 👨‍💻 Autor

**João Pedro Voges**

Desenvolvido como solução especializada para controle interno de abastecimento e gestão de frota em ambientes corporativos.
