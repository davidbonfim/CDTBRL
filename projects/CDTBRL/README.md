# CDTBRL – Stablecoin on Algorand

CDTBRL é um projeto baseado em Algorand que cria e administra um ASA (Algorand
Standard Asset) estável com controle de cunhagem, queima, transferências via
clawback e um limite rígido de oferta. O contrato foi escrito em Algopy
(Algorand Python) e exposto via interface ARC‑4.

## Visão Geral

- **Contrato principal**: `smart_contracts/algo_cdt_stable/contract.py`
- **Deploy automatizado**: `smart_contracts/algo_cdt_stable/deploy_config.py`
- **Artefatos gerados**: TEAL (`*.teal`), ARC‑56 (`*.arc56.json`) e mapas
  (`*.puya.map`)
- **Moeda**: CDTBRL (6 casas decimais, limite de 100 bilhões de unidades * 10⁶)
- **Fluxos principais**: criar ASA, adicionar/retirar minters, cunhar, queimar,
  transferir e gerenciar allowances estilo ERC‑20

## Estrutura do Projeto

```
projects/CDTBRL/
├── smart_contracts/
│   └── algo_cdt_stable/
│       ├── contract.py              # Código do smart contract (Algopy)
│       ├── deploy_config.py         # Script de deploy usado pelo AlgoKit
│       ├── AlgoCdtStable.approval.teal
│       ├── AlgoCdtStable.clear.teal
│       ├── AlgoCdtStable.arc56.json
│       └── __main__.py              # Ponto de entrada para `poetry run`
├── pyproject.toml                   # Dependências (Poetry)
└── README.md                        # Este documento
```

## Pré-requisitos

- Python 3.12+
- Poetry 1.5+
- AlgoKit CLI 2.3+ (`algokit --version`)
- Conta Algorand com fundos na rede alvo (testnet/mainnet)
- Docker (opcional, somente para LocalNet)

## Setup Rápido

```bash
# 1. Instalar dependências Python
poetry install

# 2. (opcional) Ativar o ambiente virtual
poetry shell

# 3. Compilar o contrato
algokit compile py smart_contracts/algo_cdt_stable/contract.py
# ou: algokit project run build -- algo_cdt_stable
```

## Configuração de Ambiente

O deploy espera que a mnemonic do deployer esteja exposta como variável de
ambiente `DEPLOYER_MNEMONIC`. Configure em um `.env` na raiz do projeto ou
exporte diretamente:

```bash
export DEPLOYER_MNEMONIC="palavra1 palavra2 ... palavra25"
```

Outras variáveis opcionais (consulte AlgoKit docs):

- `ALGOD_SERVER`, `ALGOD_TOKEN`, `ALGOD_PORT`
- `INDEXER_SERVER`, `INDEXER_TOKEN`, `INDEXER_PORT`

Se não forem informadas, o AlgoKit usa endpoints padrão para localnet/testnet.

## Compilação

O comando abaixo gera TEAL, mapas e especificação ARC‑56 sincronizados com o
contrato:

```bash
algokit compile py smart_contracts/algo_cdt_stable/contract.py
```

Inclua este passo sempre que modificar `contract.py` antes de qualquer deploy.

## Deploy

Todos os fluxos de deploy usam `deploy_config.py`, que:

1. Cria ou atualiza a aplicação inteligente (`AlgoCdtStable`).
2. Financia o endereço da aplicação com 1 ALGO (necessário para taxas das inner
   transactions).
3. Chama `create_asa` com os parâmetros padrão e registra o asset id no estado
   global.

### LocalNet

```bash
algokit localnet start
algokit project deploy localnet --algo_cdt_stable
```

### Testnet

```bash
algokit project deploy testnet --algo_cdt_stable
```

### Mainnet

Revise os parâmetros (limite, reserva, minters) antes de executar:

```bash
algokit project deploy mainnet --algo_cdt_stable
```

Após o deploy, verifique a aplicação e o ASA:

```bash
algokit app inspect --app-id <ID> --network testnet
```

## Uso do Smart Contract

| Método                        | Quem pode chamar                        | Descrição                                               |
|------------------------------|-----------------------------------------|---------------------------------------------------------|
| `create_asa(name, …)`        | Somente o criador do app                | Cria o ASA, define cap, reserva e guarda o asset id     |
| `set_asset(asset_id, addr)`  | Somente o criador                       | Associa ASA existente e reconfigura clawback            |
| `mint(to, amount)`           | Minter autorizado                       | Cunha tokens (sujeito ao `cap`)                         |
| `burn(amount)`               | Qualquer holder                         | Queima da própria conta                                 |
| `burn_from(account, amount)` | Quem tiver allowance                     | Queima em nome de outro (similar a ERC‑20)              |
| `transfer(to, amount)`       | Qualquer holder                         | Transfere via clawback                                  |
| `transfer_from(from, to, amt)`| Spender com allowance                  | Transfere utilizando allowance                          |
| `approve(spender, amount)`   | Qualquer holder                         | Define allowance                                        |
| `add_minter(account)`        | Minter atual (inclui criador)           | Adiciona novo minter                                    |
| `remove_minter(account)`     | Minter atual                            | Remove minter (não pode remover a si mesmo)             |
| `is_minter(account)`         | Todos                                   | Consulta minters                                        |
| `get_total_supply()`         | Todos                                   | Retorna supply cunhado                                  |
| `get_cap()`                  | Todos                                   | Retorna cap                                             |
| `set_reserve(addr)`          | Criador                                 | Atualiza endereço de reserva                            |

### Exemplos com AlgoKit Client

```python
from smart_contracts.artifacts.algo_cdt_stable.algo_cdt_stable_client import (
    AlgoCdtStableClient,
    MintArgs,
)

client = AlgoCdtStableClient(
    algod_client=algorand.client.algod,
    app_id=<ID>,
    sender=<conta_minter>,
)

# Mint 100 tokens (6 casas decimais)
client.mint(MintArgs(to=<destino>, amount=100_000_000))

# Aprovar spender
client.approve(spender=<addr>, amount=1_000_000_000)
```

### Chamadas ABI via CLI

```bash
algokit app call \
  --app-id <ID> \
  --method "mint(address,uint64)void" \
  --arg "address:<DESTINO>" \
  --arg "uint64:1000000" \
  --from <conta_minter> \
  --network testnet
```

## Financiamento dos Endereços

- **Endereço da aplicação**: precisa de saldo para inner transactions (taxas).
  O deploy já envia 1 ALGO, mas em chamadas manuais lembre-se de abastecer.
- **Reserva (reserve)**: é a conta de onde as cunhagens saem. Deve fazer opt-in
  ao ASA e possuir o supply total (cap) reservado. Ajuste conforme o seu fluxo.

Para enviar ALGO na testnet:

```bash
algokit send payment \
  --from <conta_deployer> \
  --to <app_address> \
  --amount 0.2 \
  --network testnet
```

## Testes e Qualidade

- Adicione cenários em `smart_contracts/tests/`.
- Execute com `poetry run pytest`.
- Sempre compile (`algokit compile py ...`) antes de enviar alterações.

## Troubleshooting

- **`overspend` em inner tx**: abasteça o endereço da aplicação (≥ 0.2 ALGO).
- **`DEPLOYER_MNEMONIC` ausente**: exporte a variável ou crie um `.env`.
- **Compilação falha (`created_asset_id`)**: use a sintaxe `result.created_asset.id`
  conforme implementado no contrato.
- **ASA não aparece na carteira**: faça opt-in do ativo na conta desejada.

## Recursos Úteis

- [Algorand Developer Portal](https://developer.algorand.org/)
- [AlgoKit CLI Docs](https://github.com/algorandfoundation/algokit-cli/tree/main/docs)
- [Algopy / Puya](https://github.com/algorandfoundation/puya)
- [AlgoKit Utils Python](https://github.com/algorandfoundation/algokit-utils-py)

---

Dúvidas ou sugestões? Abra uma issue ou entre em contato com a equipe. Bons
desenvolvimentos!
