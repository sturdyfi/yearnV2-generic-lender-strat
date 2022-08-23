import pytest
from brownie import Wei, config, Contract

@pytest.fixture
def whale(accounts):
    # big binance14 wallet
    acc = accounts.at("0x28c6c06298d514db089934071355e5743bf21d60", force=True)
    yield acc

@pytest.fixture()
def strategist(accounts, whale, usdc):
    decimals = usdc.decimals()
    usdc.transfer(accounts[1], 100_000 * (10 ** decimals), {"from": whale})
    yield accounts[1]

@pytest.fixture
def gov(accounts):
    yield accounts[3]

@pytest.fixture
def rando(accounts):
    yield accounts[9]

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

# specific addresses
@pytest.fixture
def usdc(interface):
    yield interface.ERC20("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")

@pytest.fixture
def sUsdc(interface):
    yield interface.IAToken("0x51D5c5D784334a4b52a07AC13D9db79cBefa1642")

@pytest.fixture
def lendingPool(interface):
    yield interface.ILendingPool("0xA422CA380bd70EeF876292839222159E41AAEe17")

@pytest.fixture
def lendingPoolConfigurator(accounts):
    yield accounts.at("0x46339B1B9bC2145FCd272AFc99002a931f8C2cFf", force=True)


@pytest.fixture
def vault(gov, rewards, guardian, usdc, pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.deploy({"from": guardian})
    vault.initialize(usdc, gov, rewards, "", "")
    vault.setManagementFee(0, {"from": gov})
    yield vault


@pytest.fixture
def strategy(
    strategist,
    gov,
    rewards,
    keeper,
    vault,
    Strategy,
    GenericSturdy
):
    strategy = strategist.deploy(Strategy, vault)
    strategy.setKeeper(keeper, {"from": gov})
    strategy.setWithdrawalThreshold(0, {"from": gov})
    strategy.setRewards(rewards, {"from": strategist})

    sturdyPlugin = strategist.deploy(GenericSturdy, strategy, "Sturdy")
    strategy.addLender(sturdyPlugin, {"from": gov})
    assert strategy.numLenders() == 1

    yield strategy
