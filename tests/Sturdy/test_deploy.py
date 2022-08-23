import random
import brownie

def test_deploy(GenericSturdy, strategy, usdc, sUsdc, lendingPool):

    sturdyPlugin = GenericSturdy.at(strategy.lenders(strategy.numLenders() - 1))

    aToken = sturdyPlugin.aToken()
    allowance = usdc.allowance(sturdyPlugin.address, lendingPool)

    assert aToken == sUsdc
    assert allowance == 2**256-1

def test_adding_plugIn(
    GenericSturdy,
    strategy,
    vault
):
    sturdyPlugin = GenericSturdy.at(strategy.lenders(strategy.numLenders() - 1))
    assert strategy.numLenders() == 1
    assert sturdyPlugin.strategy() == strategy.address
    assert sturdyPlugin.want() == strategy.want()
    assert sturdyPlugin.vault() == vault.address

def test_reinitialize(
    GenericSturdy,
    strategy,
    gov
):
    sturdyPlugin = GenericSturdy.at(strategy.lenders(strategy.numLenders() - 1))
    with brownie.reverts():
        sturdyPlugin.initialize({'from': gov})