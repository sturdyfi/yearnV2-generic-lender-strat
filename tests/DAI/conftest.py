import pytest
from brownie import Wei, config, Contract




# change these fixtures for generic tests
@pytest.fixture
def currency(dai, usdc, weth):
    yield dai


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass


@pytest.fixture
def whale(accounts,currency, web3, weth):

    # big avalanche bridge wallet
    acc = accounts.at("0xE78388b4CE79068e89Bf8aA7f218eF6b9AB0e9d0", force=True)
    assert currency.balanceOf(acc) > 0


    assert weth.balanceOf(acc) > 0
    yield acc


@pytest.fixture()
def strategist(accounts, whale, currency):
    decimals = currency.decimals()
    currency.transfer(accounts[1], 100_000 * (10 ** decimals), {"from": whale})
    yield accounts[1]


@pytest.fixture
def samdev(accounts):
    yield accounts.at("0xC3D6880fD95E06C816cB030fAc45b3ffe3651Cb0", force=True)


@pytest.fixture
def gov(accounts):
    yield accounts[3]


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]


@pytest.fixture
def rando(accounts):
    yield accounts[9]


# specific addresses
@pytest.fixture
def usdc(interface):
    yield interface.ERC20("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")


@pytest.fixture
def dai(interface):
    yield interface.ERC20("0x6b175474e89094c44da98b954eedeac495271d0f")


@pytest.fixture
def weth(interface):
    yield interface.IWETH("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")


@pytest.fixture
def cdai(interface):
    yield interface.CErc20I("0x5d3a536e4d6dbd6114cc1ead35777bab948e3643")


@pytest.fixture
def cUsdc(interface):
    yield interface.CErc20I("0x39AA39c021dfbaE8faC545936693aC917d5E7563")


@pytest.fixture
def crUsdc(interface):
    yield interface.CErc20I("0x44fbeBd2F576670a6C33f6Fc0B00aA8c5753b322")


@pytest.fixture
def aUsdc(interface):
    yield interface.IAToken("0xBcca60bB61934080951369a648Fb03DF4F96263C")


@pytest.fixture(scope="module", autouse=True)
def shared_setup(module_isolation):
    pass


@pytest.fixture
def vault(gov, rewards, guardian, currency, pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.deploy({"from": guardian})
    vault.initialize(currency, gov, rewards, "", "")
    vault.setManagementFee(0, {"from": gov})
    
    vault.setDepositLimit(2**256-1, {"from": gov})
    yield vault


@pytest.fixture
def strategy(
    strategist,
    gov,
    rewards,
    keeper,
    vault,
    Strategy,
):
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper, {"from": gov})
    strategy.setWithdrawalThreshold(0, {"from": gov})
    strategy.setRewards(rewards, {"from": strategist})

    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 - 1, 1000, {"from": gov})

    yield strategy
