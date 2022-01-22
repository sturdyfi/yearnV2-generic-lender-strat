from itertools import count
from brownie import Wei, reverts
from useful_methods import genericStateOfVault, genericStateOfStrat

def test_normal_activity(
    accounts,
    Contract,
    GenericIronBank
):
    gov = accounts.at('0xC0E2830724C946a6748dDFE09753613cd38f6767', force=True)

    #yfi
    yfi_vault = Contract('0x2C850cceD00ce2b14AA9D658b7Cad5dF659493Db')
    old_ftm_cream = Contract('0x4b4FCEA3dfC646937B28cBDAa49bDEac5d190719')
    scream_plugin = Contract('0xcf86023D284751d1bbBD98554Cff0E4912553836')
    yfi_genlender = Contract('0xdf262b43bea0acd0dd5832cf2422e0c9b2c539dc')
    manualAll = [[old_ftm_cream, 900], [scream_plugin, 100]]
    yfi_genlender.manualAllocation(manualAll, {"from": gov})
    print_lenders(yfi_genlender)
    
    crYFI = Contract('0x0980f2F0D2af35eF2c4521b2342D59db575303F7')
    yfi_genlender.safeRemoveLender(old_ftm_cream, {'from': gov})
    print_lenders(yfi_genlender)

    ibPlugin = gov.deploy(GenericIronBank, yfi_genlender, "IB Lender YFI", crYFI)
    yfi_genlender.addLender(ibPlugin, {'from': gov})
    manualAll = [[ibPlugin, 900], [scream_plugin, 100]]
    yfi_genlender.manualAllocation(manualAll, {"from": gov})
    print_lenders(yfi_genlender)

    #dai
    dai_vault = Contract('0x637eC617c86D24E421328e6CAEa1d92114892439')
    dai_genlender = Contract('0xd025b85db175ef1b175af223bd37f330db277786')
    old_ftm_cream = Contract('0x776C0Bd1438290fB97781309B18Cd96B78548688')
    crDAI = Contract('0x04c762a5dF2Fa02FE868F25359E0C259fB811CfE')
    dai_genlender.safeRemoveLender(old_ftm_cream, {'from': gov})
    print_lenders(dai_genlender)

    #wftm
    wftm_vault = Contract('0x0DEC85e74A92c52b7F708c4B10207D9560CEFaf0')
    wftm_genlender = Contract('0x695A4a6e5888934828Cb97A3a7ADbfc71A70922D')
    old_ftm_cream = Contract('0xAc3Fb94061FFfa8A459586Fa7d90fa0d6B8cd0e6')
    crWFTM = Contract('0xd528697008aC67A21818751A5e3c58C8daE54696')
    wftm_genlender.safeRemoveLender(old_ftm_cream, {'from': gov})
    print_lenders(wftm_genlender)


def print_lenders(strategy, decimals=18):
    form = "{:.2%}"
    formS = "{:,.2f}"

    status = strategy.lendStatuses()
    print("  Gen Lender Real APRs:")

    for j in status:
        print(
            f"    Lender: {j[0]}, Deposits: {formS.format(j[1]/(10 ** decimals))}, APR: {form.format(j[2]/(1e18))}"
        )
