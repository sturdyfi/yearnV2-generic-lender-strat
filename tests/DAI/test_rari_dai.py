from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfStrat, genericStateOfVault, deposit, sleep
import random
import brownie


def test_rari_dai(strategy, web3, chain, vault, Contract, interface, GenericCream, currency, whale, strategist, gov):
    fuse_pool_directory = interface.FusePoolDirectory('0x835482FE0532f169024d5E9410199369aAD5C77E')
    #fuse_pool_lens = interface.FusePoolLens('0x6Dc585Ad66A10214Ef0502492B0CC02F0e836eec')
    #(num, public_poools) = fuse_pool_directory.getPublicPools()
    our_pools = [18]
    plugins = []

    plugin = strategist.deploy(GenericCream, strategy, 'Olympus Pool Party', "0x8E4E0257A4759559B4B1AC087fe8d80c63f20D19")
    strategy.addLender(plugin, {"from": gov})


    plugin = strategist.deploy(GenericCream, strategy, 'Tetranodes Pool', "0x989273ec41274C4227bCB878C2c26fdd3afbE70d")
    strategy.addLender(plugin, {"from": gov})
    #for i in our_pools:
    #    print(public_poools[i])
    #    comptroller = interface.ComptrollerI(public_poools[i][2])
    #    
    #    all_markets = comptroller.getAllMarkets()
    #    for j in all_markets:
    #        if interface.CErc20I(j).underlying() == currency:
    #            print("yes ", j)
    #            ctoken = j
    #            break

    #    plugin = strategist.deploy(GenericCream, strategy, public_poools[i][0], ctoken)
    #    strategy.addLender(plugin, {"from": gov})
    #    plugins.append(plugin)

    currency.approve(vault, 2 ** 256 - 1, {"from": whale})
    deposit_amount = 5_000_000 *1e18
    vault.deposit(deposit_amount, {"from": whale})
    form = "{:.2%}"
    formS = "{:,.0f}"

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    deposit_amount = 1_000_000 *1e18
    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )
    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    vault.deposit(deposit_amount, {"from": whale})
    strategy.harvest({'from': strategist})

    status = strategy.lendStatuses()

    for j in status:
        print(
            f"Lender: {j[0]}, Deposits: {formS.format(j[1]/1e18)}, APR: {form.format(j[2]/1e18)}"
        )

    