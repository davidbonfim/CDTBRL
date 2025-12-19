import { Config } from '@algorandfoundation/algokit-utils'
import { registerDebugEventHandlers } from '@algorandfoundation/algokit-utils-debug'
import { algorandFixture } from '@algorandfoundation/algokit-utils/testing'
import { Address } from 'algosdk'
import { beforeAll, beforeEach, describe, expect, test } from 'vitest'
import { DucielloGroupGoldAsaFactory } from '../artifacts/duciello_group_gold_asa/DucielloGroupGoldAsaClient'

describe('DucielloGroupGoldAsa contract', () => {
  const localnet = algorandFixture()
  beforeAll(() => {
    Config.configure({
      debug: true,
      // traceAll: true,
    })
    registerDebugEventHandlers()
  })
  beforeEach(localnet.newScope)

  const deploy = async (account: Address) => {
    const factory = localnet.algorand.client.getTypedAppFactory(DucielloGroupGoldAsaFactory, {
      defaultSender: account,
    })

    const { appClient } = await factory.deploy({
      onUpdate: 'append',
      onSchemaBreak: 'append',
    })

    // ASA creation will be executed from the app account (inner txn sender), so ensure it has balance.
    await localnet.algorand.send.payment({
      sender: account,
      receiver: appClient.appAddress,
      amount: (1).algo(),
    })
    return { client: appClient }
  }

  test('creates GOLD ASA', async () => {
    const { testAccount } = localnet.context
    const { client } = await deploy(testAccount)

    const result = await client.send.createGoldAsset()

    expect(result.return).toBeGreaterThan(0)
  })

  test('simulate createGoldAsset with correct budget consumed', async () => {
    const { testAccount } = localnet.context
    const { client } = await deploy(testAccount)
    const result = await client
      .newGroup()
      .createGoldAsset()
      .simulate()

    expect(result.returns[0]).toBeGreaterThan(0)
    expect(result.simulateResponse.txnGroups[0].appBudgetConsumed).toBeLessThan(100)
  })
})
