# AlgoCdtStable Smart Contract

Este é um smart contract para uma stablecoin (CDTBRL) na blockchain Algorand, implementando funcionalidades similares ao ERC-20 com controles de minting/burning e um teto de suprimento.

## Especificações do Contrato

- **Nome**: CDTBRL
- **Símbolo**: CDTBRL
- **Decimais**: 6 (para precisão de stablecoin)
- **Teto (Cap)**: 100.000.000.000 * 10^6 tokens (100 bilhões de tokens)
- **ASA (Algorand Standard Asset)**: Criada automaticamente no deploy, com clawback controlado pelo contrato
- **Reserve Address**: Endereço inicial definido no deploy (padrão: deployer)
- **Minters**: Lista de endereços autorizados a mintar tokens (inicialmente apenas o deployer)
- **Funcionalidades**:
  - `create_asa`: Cria a ASA (apenas deployer)
  - `mint`: Cria novos tokens (apenas minters)
  - `burn` / `burn_from`: Queima tokens
  - `transfer` / `transfer_from`: Transfere tokens
  - `approve` / `allowance`: Sistema de aprovações para transferências delegadas
  - `add_minter` / `remove_minter`: Gerencia minters
  - `get_total_supply` / `get_cap`: Consulta suprimento
  - `balance_of`: Placeholder (consulta externa necessária via indexer)
- **Limitações**: `balance_of` retorna 0 (use indexer da Algorand para saldos reais)

## Pré-requisitos

- AlgoKit instalado (`pip install algokit`)
- Conta Algorand com ALGO (para transações)
- Ambiente configurado (.env com DEPLOYER_MNEMONIC, ALGOD_SERVER, etc.)

## Deploy do Contrato

### Via Terminal (Localnet/Testnet)

1. Inicie o localnet (se usar sandbox local):
   ```
   algokit localnet start
   ```

2. Configure o `.env` (exemplo para localnet):
   ```
   DEPLOYER_MNEMONIC=sua_mnemonica_aqui
   ALGOD_SERVER=http://localhost:4001
   ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
   INDEXER_SERVER=http://localhost:8980
   INDEXER_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
   ```

3. Feche a conta (se necessário):
   ```
   algokit dispenser
   ```

4. Execute o deploy:
   ```
   cd projects/CDTBRL
   python -m smart_contracts deploy
   ```
   - Isso implanta o app, cria a ASA e registra os IDs nos logs.

## Interações com o Contrato

### Via Python (Recomendado - Cliente Gerado)

Use o cliente gerado pelo AlgoKit para interações fáceis.

1. Crie um script `interact.py` em `projects/CDTBRL/smart_contracts/algo_cdt_stable/`:

   ```python
   import algokit_utils
   from smart_contracts.artifacts.algo_cdt_stable.algo_cdt_stable_client import (
       MintArgs, TransferArgs, AlgoCdtStableFactory
   )

   algorand = algokit_utils.AlgorandClient.from_environment()
   deployer = algorand.account.from_environment("DEPLOYER")

   factory = algorand.client.get_typed_app_factory(
       AlgoCdtStableFactory, default_sender=deployer.address
   )
   app_client = factory.get_app_client(app_id=SEU_APP_ID)  # Substitua pelo ID do app

   # Exemplo: Mintar tokens
   response = app_client.send.mint(
       args=MintArgs(to="ENDERECO_DESTINO", amount=1000000)  # 1 CDTBRL
   )
   print(f"Mintado: {response}")

   # Exemplo: Transferir tokens
   response = app_client.send.transfer(
       args=TransferArgs(to="ENDERECO_DESTINO", amount=500000)  # 0.5 CDTBRL
   )
   print(f"Transferido: {response}")

   # Exemplo: Consultar suprimento total
   total = app_client.send.get_total_supply()
   print(f"Suprimento total: {total.abi_return}")
   ```

2. Execute:
   ```
   python smart_contracts/algo_cdt_stable/interact.py
   ```

### Via PHP

Use a biblioteca `algorand-php` para interações manuais via ABI.

1. Instale: `composer require algorand/algorand-php`

2. Crie um script `interact.php`:

   ```php
   <?php
   require 'vendor/autoload.php';

   use Algorand\Algorand;

   $algorand = new Algorand('http://localhost:4001', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa');
   $mnemonic = 'SUA_MNEMONICA_AQUI';
   $account = $algorand->account->mnemonicToPrivateKey($mnemonic);

   $appId = SEU_APP_ID;  // ID do app
   $assetId = SEU_ASSET_ID;  // ID da ASA

   // Exemplo: Mintar tokens
   $txn = $algorand->applicationCallTransaction(
       $account->getAddress(),
       $appId,
       [
           'method' => 'mint',
           'args' => [
               ['type' => 'address', 'value' => 'ENDERECO_DESTINO'],
               ['type' => 'uint64', 'value' => 1000000]  // 1 CDTBRL
           ]
       ]
   );
   $signedTxn = $txn->sign($account);
   $response = $algorand->sendTransaction($signedTxn);
   echo 'Mintado: ' . $response['txId'] . PHP_EOL;

   // Exemplo: Transferir tokens
   $txn = $algorand->applicationCallTransaction(
       $account->getAddress(),
       $appId,
       [
           'method' => 'transfer',
           'args' => [
               ['type' => 'address', 'value' => 'ENDERECO_DESTINO'],
               ['type' => 'uint64', 'value' => 500000]  // 0.5 CDTBRL
           ]
       ]
   );
   $signedTxn = $txn->sign($account);
   $response = $algorand->sendTransaction($signedTxn);
   echo 'Transferido: ' . $response['txId'] . PHP_EOL;

   // Exemplo: Consultar suprimento total
   $txn = $algorand->applicationCallTransaction(
       $account->getAddress(),
       $appId,
       ['method' => 'get_total_supply']
   );
   $simulated = $algorand->simulateTransaction($txn);
   echo 'Suprimento total: ' . $simulated['returnValue'] . PHP_EOL;
   ?>
   ```

3. Execute: `php interact.php`

### Via Terminal (Comandos Diretos)

Use `algokit` para interações básicas (menos flexível).

1. Para consultar estado:
   ```
   algokit doctor  # Verifica configuração
   ```

2. Para enviar transações manuais, use `goal` (se instalado) ou scripts Python/PHP acima.

3. Verifique saldos no explorer local: `http://localhost:4002`

## Testes e Verificação

- Após interações, verifique transações no explorer.
- Teste casos extremos: mintar além do cap (deve falhar), transferir sem saldo, etc.
- Use `algokit localnet reset` para reiniciar testes.

## Suporte

Para dúvidas, consulte a documentação do AlgoKit ou Algorand Developer Docs.