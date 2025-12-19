import { AlgorandClient } from '@algorandfoundation/algokit-utils'
import { DucielloGroupGoldAsaFactory } from '../artifacts/duciello_group_gold_asa/DucielloGroupGoldAsaClient'

// Below is a showcase of various deployment options you can use in TypeScript Client
export async function deploy() {
  console.log('=== Deploying DucielloGroupGoldAsa ===')

  const algorand = AlgorandClient.fromEnvironment()
  const deployer = await algorand.account.fromEnvironment('DEPLOYER')

  const factory = algorand.client.getTypedAppFactory(DucielloGroupGoldAsaFactory, {
    defaultSender: deployer.addr,
  })

  const { appClient, result } = await factory.deploy({ onUpdate: 'append', onSchemaBreak: 'append' })

  // If app was just created fund the app account
  if (['create', 'replace'].includes(result.operationPerformed)) {
    await algorand.send.payment({
      amount: (1).algo(),
      sender: deployer.addr,
      receiver: appClient.appAddress,
    })
  }

  const existingGoldAssetId = await appClient.state.global.goldAssetId()
  if (existingGoldAssetId) {
    console.log(`GOLD ASA already created; goldAssetId=${existingGoldAssetId}`)
    return
  }

  const response = await appClient.send.createGoldAsset({ coverAppCallInnerTransactionFees: true })
  console.log(`Created GOLD ASA; goldAssetId=${response.return}`)
}
