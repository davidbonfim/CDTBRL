import {
  Bytes,
  Contract,
  GlobalState,
  Global,
  Txn,
  assert,
  arc4,
  gtxn,
  itxn,
  log,
  uint64,
} from '@algorandfoundation/algorand-typescript'

const GOLD_ASA_URL = 'https://www.duciello.com.br/'
const GOLD_ARC3_URL =
  'https://raw.githubusercontent.com/davidbonfim/CDTBRL/main/projects/gold-duciello-group/assets/arc3/duciello-group-gold.json#arc3'
const GOLD_ARC3_METADATA_HASH = Bytes.fromHex('887b2793e193f76debcc2f8c3030a1e7065b3e7929dae45d894159b47d7bbae0', {
  length: 32,
})

export class DucielloGroupGoldAsa extends Contract {
  // Armazena o ID do token de ouro criado pelo contrato
  public goldAssetId = GlobalState<uint64>()

  @arc4.abimethod()
  public createGoldAsset(): uint64 {
    assert(Txn.sender.bytes === Global.creatorAddress.bytes, 'Apenas o criador pode criar o ativo GOLD')
    assert(!this.goldAssetId.hasValue, 'Ativo GOLD já foi criado')

    const result = itxn
	      .assetConfig({
	        assetName: 'Duciello Group Gold',
	        unitName: 'GOLD',
	        total: 40_000_000, // 40 toneladas (1 token = 1 grama)
	        decimals: 0, // 1 token = 1 grama
	        url: GOLD_ASA_URL,
	        metadataHash: GOLD_ARC3_METADATA_HASH,
	        note: GOLD_ARC3_URL,
        manager: Global.currentApplicationAddress,
        reserve: Global.currentApplicationAddress,
        freeze: Global.currentApplicationAddress,
        clawback: Global.currentApplicationAddress,
      })
      .submit()

    const createdId = result.createdAsset.id
    this.goldAssetId.value = createdId

    log('gold_asset_created', createdId)
    return createdId
  }

  @arc4.abimethod()
  public redeemGold(axfer: gtxn.AssetTransferTxn): void {
    assert(this.goldAssetId.hasValue, 'Ativo GOLD ainda não foi criado')

    assert(axfer.xferAsset.id === this.goldAssetId.value, 'Ativo inválido para resgate')
    assert(
      axfer.assetReceiver.bytes === Global.currentApplicationAddress.bytes,
      'O destino do axfer deve ser o contrato',
    )
    assert(axfer.sender.bytes === Txn.sender.bytes, 'O sender do axfer deve ser o chamador')
    assert(axfer.assetAmount > 0, 'Quantidade inválida para resgate')
    assert(
      axfer.assetSender.bytes === Global.zeroAddress.bytes,
      'Resgate não permite clawback (assetSender deve ser zero)',
    )
    assert(
      axfer.assetCloseTo.bytes === Global.zeroAddress.bytes,
      'Resgate não permite close-to (assetCloseTo deve ser zero)',
    )

    // Log para auditoria off-chain (ex.: backend escuta logs para iniciar logística de resgate físico)
    log('gold_redeem_request', Txn.sender, axfer.assetAmount, axfer.txnId)
  }
}
