# Manual de uso do ChatDebBot

O ChatDebBot ajuda você a controlar cobranças pelo WhatsApp. Com ele, você
pode cadastrar valores que alguém deve, consultar cobranças, registrar
pagamentos e receber lembretes no dia do vencimento.

━━━━━━━━━━━━━━━━━━

## 🚀 COMEÇANDO

Envie uma saudação, como:

- `Oi`
- `Olá`
- `Oie`

O bot responderá com três opções:

- **Cadastrar cobrança**
- **Listar cobranças**
- **Atualizar cobrança**

━━━━━━━━━━━━━━━━━━

## 💰 CADASTRAR UMA COBRANÇA

Clique em **Cadastrar cobrança** e envie o valor e o nome da pessoa.

Exemplo:

```text
500 Fabio
```

Também é possível escrever uma frase completa:

```text
O Fabio me deve 500 reais para daqui 30 dias
```

O bot mostrará os dados da cobrança e perguntará se está tudo certo.

Clique em **Confirmar Dívida** para salvar ou em **Recusar Dívida** para
cancelar.

Depois da confirmação, a cobrança ficará registrada como **Em aberto**.

### 📅 Informando o vencimento

Você pode usar qualquer um destes formatos:

```text
500 Fabio para 30 dias
```

ou:

```text
500 Fabio para daqui 30 dias
```

Se nenhum prazo for informado, o bot usa a data atual como vencimento.

### 📝 Adicionando uma descrição

Você pode adicionar uma descrição após um hífen:

```text
500 Fabio para 30 dias - almoço
```

Ou usando o campo `descrição`:

```text
500 Fabio para 30 dias descrição: almoço
```

A descrição aparecerá na confirmação, na listagem e nos lembretes.

━━━━━━━━━━━━━━━━━━

## 📋 LISTAR COBRANÇAS

Clique em **Listar cobranças**.

Quando o bot pedir o nome, envie somente o nome da pessoa:

```text
Fabio
```

Para ver todas as cobranças em aberto cadastradas por você, envie:

```text
Todas
```

A listagem mostra:

- Nome do devedor
- Descrição
- Valor
- Data de vencimento
- Situação da cobrança
- Total em aberto

Cobranças marcadas como **Pago** não aparecem na lista de valores em aberto.

🔒 Cada usuário vê somente as próprias cobranças.

━━━━━━━━━━━━━━━━━━

## 👥 NOMES PARECIDOS

O bot ignora diferenças de acentuação para encontrar nomes. Por exemplo,
`Fabio` e `Fábio` podem ser considerados a mesma pessoa.

Se houver mais de uma cobrança ou pessoa possível, o bot perguntará:

> É sobre qual dessas cobranças?

ou:

> Encontrei mais de uma pessoa parecida. Qual delas você quis dizer?

Selecione o botão correspondente à cobrança ou ao nome desejado. A ação
continuará usando a opção escolhida.

━━━━━━━━━━━━━━━━━━

## ✅ REGISTRANDO UM PAGAMENTO

Você pode informar diretamente que alguém pagou:

```text
O Jorge me pagou 500 reais
```

O bot procurará uma cobrança em aberto correspondente e a marcará como
**Pago**.

Se houver mais de uma cobrança possível, o bot mostrará os detalhes e pedirá
que você confirme qual cobrança foi paga.

Assim, o pagamento não cria uma nova cobrança e não altera uma cobrança
diferente por engano.

━━━━━━━━━━━━━━━━━━

## 🔔 LEMBRETES DE VENCIMENTO

No dia do vencimento, o bot enviará uma mensagem lembrando você da cobrança.

Exemplo:

```text
Lembrete: você tem uma cobrança de R$500,00 para Fabio.
Descrição: almoço.
Essa cobrança já foi paga?
```

Se a pessoa já tiver pago, clique em **Já pagou**.

A cobrança será atualizada para **Pago** e deixará de aparecer como valor em
aberto.

━━━━━━━━━━━━━━━━━━

## ❓ SITUAÇÕES COMUNS

### O bot não entendeu a mensagem

Envie uma frase mais direta, contendo:

- O valor
- O nome da pessoa
- O prazo, se necessário
- A descrição, se desejada

Exemplo:

```text
O Fabio me deve 500 reais para daqui 30 dias - almoço
```

### Quero começar novamente

Envie `Oi` para abrir o menu principal novamente.

### Escolhi a opção errada

Envie `Oi` para abrir o menu outra vez e escolher uma nova opção.

### Quero consultar uma pessoa específica

Clique em **Listar cobranças** e envie somente o nome:

```text
Fabio
```

### Quero consultar todas as pessoas

Clique em **Listar cobranças** e envie:

```text
Todas
```

━━━━━━━━━━━━━━━━━━

## ⚠️ OBSERVAÇÃO

A opção **Atualizar cobrança** aparece no menu, mas ainda está em construção.

Por enquanto, é possível:

- Cadastrar cobranças.
- Adicionar descrições.
- Listar cobranças em aberto.
- Consultar todas as cobranças do próprio usuário.
- Registrar pagamentos.
- Receber lembretes.
- Marcar cobranças como pagas.

━━━━━━━━━━━━━━━━━━

🤖 **ChatDebBot — Controle suas cobranças de forma simples pelo WhatsApp!**
