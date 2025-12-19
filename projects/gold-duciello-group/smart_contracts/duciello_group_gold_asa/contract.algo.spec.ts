import { TestExecutionContext } from '@algorandfoundation/algorand-typescript-testing'
import { beforeEach, describe, expect, it } from 'vitest'
import { DucielloGroupGoldAsa } from './contract.algo'

describe('DucielloGroupGoldAsa contract', () => {
  const ctx = new TestExecutionContext()

  beforeEach(() => {
    ctx.reset()
  })

  it('Creates the GOLD ASA via inner transaction and stores goldAssetId', () => {
    const creator = ctx.any.account()
    ctx.defaultSender = creator

    const contract = ctx.contract.create(DucielloGroupGoldAsa)
    expect(contract.goldAssetId.hasValue).toBe(false)

    const createdId = contract.createGoldAsset()

    expect(createdId.valueOf()).toBeGreaterThan(0n)
    expect(contract.goldAssetId.value).toBe(createdId)
  })

  it('Only the app creator can call createGoldAsset', () => {
    const creator = ctx.any.account()
    const attacker = ctx.any.account()

    ctx.defaultSender = creator
    const contract = ctx.contract.create(DucielloGroupGoldAsa)

    ctx.defaultSender = attacker
    expect(() => contract.createGoldAsset()).toThrow(/criador/i)
  })
})
