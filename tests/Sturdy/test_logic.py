import random
import brownie
from useful_methods import deposit, sleep, close

def test_logic(
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
    
    #Deposit
    amount = 10_000 * (10 ** decimals)
    deposit(amount, whale, usdc, vault)

    strategy.harvest({"from":gov})
    assert sturdyPlugin.hasAssets() == True
    assert sturdyPlugin.nav() >= amount * .999
    assert sturdyPlugin.nav() == sturdyPlugin.underlyingBalanceStored()

    deposit(amount, whale, usdc, vault)
    apr = sturdyPlugin.apr()
    aprAfter = sturdyPlugin.aprAfterDeposit(amount)
    assert apr > aprAfter

    strategy.harvest({"from":gov})
    newApr = sturdyPlugin.apr()
    assert close(aprAfter, newApr)

    nav = sturdyPlugin.nav()

    # making yield in sturdy pool
    usdc.approve(lendingPool, 1000 * (10 ** (decimals)), {"from": whale})
    lendingPool.registerVault(whale, {"from": lendingPoolConfigurator})
    lendingPool.depositYield(usdc.address, 1000 * (10 ** (decimals)), {"from": whale})
    sleep(chain, 10)

    newNav = sturdyPlugin.nav()
    assert newNav > nav

    #withdraw Some
    usdcBal = usdc.balanceOf(whale.address)
    vault.withdraw(amount, {"from": whale})
    usdcAfterBal = usdc.balanceOf(whale.address)
    assert usdcBal + amount <= usdcAfterBal

    a = sturdyPlugin.apr()
    n = sturdyPlugin.nav()

    assert sturdyPlugin.weightedApr() ==  a * n

    #withdraw all
    usdcBal = usdc.balanceOf(whale.address)
    sleep(chain, 100)
    vault.withdraw({"from":whale})
    usdcAfterBal = usdc.balanceOf(whale.address)

    assert usdcBal + amount <= usdcAfterBal

def test_emergency_withdraw(
    GenericSturdy,
    vault,
    strategy,
    gov,
    rando,
    usdc,
    whale,
    chain
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

    with brownie.reverts():
        sturdyPlugin.emergencyWithdraw(sturdyPlugin.nav(), {"from":rando})

    usdcBal = usdc.balanceOf(gov.address)
    toWithdraw = amount * .1
    sturdyPlugin.emergencyWithdraw(toWithdraw, {"from":gov})
    usdcBalAfter = usdc.balanceOf(gov.address)
    assert usdcBalAfter - toWithdraw == usdcBal

    usdcBal = usdc.balanceOf(gov.address)
    nav = sturdyPlugin.nav()
    sturdyPlugin.emergencyWithdraw(nav, {"from":gov})
    usdcBalAfter = usdc.balanceOf(gov.address)
    assert usdcBalAfter - nav == usdcBal

def test__withdrawAll(
    GenericSturdy,
    vault,
    strategy,
    gov,
    rando,
    usdc,
    whale,
    chain
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

    with brownie.reverts():
        sturdyPlugin.withdrawAll({"from":rando})

    usdcBal = usdc.balanceOf(sturdyPlugin.address)
    sturdyPlugin.withdrawAll({"from":gov})
    
    assert sturdyPlugin.underlyingBalanceStored() == 0
    assert usdc.balanceOf(strategy.address) > usdcBal