import random
import brownie
from useful_methods import deposit, sleep

def test_setup(
    strategy
):
    trigger = strategy.harvestTrigger(1000000000)
    assert trigger == False

def test_apr(
    GenericSturdy,
    strategy,
):
    sturdyPlugin = GenericSturdy.at(strategy.lenders(strategy.numLenders() - 1))
    apr = sturdyPlugin.apr()

    assert apr > 0


def test_harvest(
    GenericSturdy,
    vault,
    strategy,
    gov,
    rando,
    usdc,
    whale,
    chain,
    lendingPool,
    lendingPoolConfigurator
):
    sturdyPlugin = GenericSturdy.at(strategy.lenders(strategy.numLenders() - 1))

    assert sturdyPlugin.hasAssets() == False
    assert sturdyPlugin.nav() == 0

    decimals = usdc.decimals()
    deposit_limit = 1_000_000_000 * (10 ** (decimals))
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 500, {"from": gov})
    vault.setDepositLimit(deposit_limit, {"from": gov})
    
    sleep(chain, 1)
    
    #Deposit
    amount = 10_000 * (10 ** decimals)
    deposit(amount, whale, usdc, vault)

    strategy.harvest({"from":gov})
    assert sturdyPlugin.hasAssets() == True
    assert sturdyPlugin.nav() >= amount * .999
    assert sturdyPlugin.nav() == sturdyPlugin.underlyingBalanceStored()

    assert strategy.harvestTrigger(1000000000) == False
    
    # making yield in sturdy pool
    usdc.approve(lendingPool, 1000 * (10 ** (decimals)), {"from": whale})
    lendingPool.registerVault(whale, {"from": lendingPoolConfigurator})
    lendingPool.depositYield(usdc.address, 1000 * (10 ** (decimals)), {"from": whale})
    
    assert strategy.harvestTrigger(1000000000) == True

    with brownie.reverts():
        strategy.harvest({"from":rando})

    aBal = sturdyPlugin.underlyingBalanceStored()

    strategy.harvest({"from":gov})
    assert aBal > sturdyPlugin.underlyingBalanceStored()