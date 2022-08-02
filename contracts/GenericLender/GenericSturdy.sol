// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import "./GenericLenderBase.sol";
import "../Interfaces/Aave/IAToken.sol";
import "../Interfaces/Aave/ILendingPool.sol";
import "../Interfaces/Aave/IPriceOracle.sol";
import "../Interfaces/Aave/IProtocolDataProvider.sol";
import "../Interfaces/Aave/IReserveInterestRateStrategy.sol";
import "../Libraries/Aave/DataTypes.sol";
import "../Interfaces/Sturdy/ISturdyAPRDataProvider.sol";

/********************
 *   A lender plugin for LenderYieldOptimiser for any stable asset on Sturdy
 *   Made by Sturdy
 *   https://github.com/sturdyfi/yearnV2-generic-lender-strat/blob/master/contracts/GenericLender/GenericSturdy.sol
 *
 ********************* */

contract GenericSturdy is GenericLenderBase {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    IProtocolDataProvider public constant protocolDataProvider = IProtocolDataProvider(address(0x960993Cb6bA0E8244007a57544A55bDdb52db97e));
    IAToken public aToken;

    address public keep3r;

    bool public isIncentivised;
    uint16 internal customReferral;

    address public constant WETH = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
    ISturdyAPRDataProvider public constant STURDY_APR_PROVIDER = ISturdyAPRDataProvider(0x8F5273205c687508347eb89f81e9b99DA3f01383);

    constructor(
        address _strategy,
        string memory name,
        IAToken _aToken,
        bool _isIncentivised
    ) public GenericLenderBase(_strategy, name) {
        _initialize(_aToken, _isIncentivised);
    }

    function initialize(IAToken _aToken, bool _isIncentivised) external {
        _initialize(_aToken, _isIncentivised);
    }

    function cloneSturdyLender(
        address _strategy,
        string memory _name,
        IAToken _aToken,
        bool _isIncentivised
    ) external returns (address newLender) {
        newLender = _clone(_strategy, _name);
        GenericSturdy(newLender).initialize(_aToken, _isIncentivised);
    }

    // for the management to activate / deactivate incentives functionality
    function setIsIncentivised(bool _isIncentivised) external management {
        // NOTE: if the aToken is not incentivised, getIncentivesController() might revert (aToken won't implement it)
        // to avoid calling it, we use the OR and lazy evaluation
        require(
            !_isIncentivised || address(aToken.getIncentivesController()) != address(0),
            "!aToken does not have incentives controller set up"
        );
        isIncentivised = _isIncentivised;
    }

    function setReferralCode(uint16 _customReferral) external management {
        require(_customReferral != 0, "!invalid referral code");
        customReferral = _customReferral;
    }

    function setKeep3r(address _keep3r) external management {
        keep3r = _keep3r;
    }

    function withdraw(uint256 amount) external override management returns (uint256) {
        return _withdraw(amount);
    }

    //emergency withdraw. sends balance plus amount to governance
    function emergencyWithdraw(uint256 amount) external override onlyGovernance {
        _lendingPool().withdraw(address(want), amount, address(this));

        want.safeTransfer(vault.governance(), want.balanceOf(address(this)));
    }

    function deposit() external override management {
        uint256 balance = want.balanceOf(address(this));
        _deposit(balance);
    }

    function withdrawAll() external override management returns (bool) {
        uint256 invested = _nav();
        uint256 returned = _withdraw(invested);
        return returned >= invested;
    }

    function nav() external view override returns (uint256) {
        return _nav();
    }

    function underlyingBalanceStored() public view returns (uint256 balance) {
        balance = aToken.balanceOf(address(this));
    }

    function apr() external view override returns (uint256) {
        return _apr();
    }

    function weightedApr() external view override returns (uint256) {
        uint256 a = _apr();
        return a.mul(_nav());
    }

    function aprAfterDeposit(uint256 extraAmount) external view override returns (uint256) {
        // i need to calculate new supplyRate after Deposit (when deposit has not been done yet)
        DataTypes.ReserveData memory reserveData = _lendingPool().getReserveData(address(want));
        (uint256 decimals, , , , , , , , , ) = protocolDataProvider.getReserveConfigurationData(address(want));
        uint256 liquidityRate = uint256(reserveData.currentLiquidityRate).div(1e9);
        uint256 newLiquidityRate = _getLiquidityRateAfterDeposit(extraAmount).div(1e9);
        uint256 sturdyVaultAPR = STURDY_APR_PROVIDER.APR(address(want)).sub(liquidityRate);
        uint256 totalBorrowableLiquidityInPrice = _getTotalBorrowableLiquidityInPrice();
        uint256 extraAmountInPrice = extraAmount.mul(_oracle().getAssetPrice(address(want))).div(10**decimals);

        sturdyVaultAPR = sturdyVaultAPR
            .mul(totalBorrowableLiquidityInPrice)
            .div(totalBorrowableLiquidityInPrice.add(extraAmountInPrice));

        return sturdyVaultAPR.add(newLiquidityRate);
    }

    function hasAssets() external view override returns (bool) {
        return aToken.balanceOf(address(this)) > 0;
    }

    function _initialize(IAToken _aToken, bool _isIncentivised) internal {
        require(address(aToken) == address(0), "GenericSturdy already initialized");

        require(
            !_isIncentivised || address(_aToken.getIncentivesController()) != address(0),
            "!aToken does not have incentives controller set up"
        );
        isIncentivised = _isIncentivised;
        aToken = _aToken;
        require(_lendingPool().getReserveData(address(want)).aTokenAddress == address(_aToken), "WRONG ATOKEN");
        IERC20(address(want)).safeApprove(address(_lendingPool()), type(uint256).max);
    }

    function _nav() internal view returns (uint256) {
        return want.balanceOf(address(this)).add(underlyingBalanceStored());
    }

    function _apr() internal view returns (uint256) {
        return STURDY_APR_PROVIDER.APR(address(want));
    }

    //withdraw an amount including any want balance
    function _withdraw(uint256 amount) internal returns (uint256) {
        uint256 balanceUnderlying = aToken.balanceOf(address(this));
        uint256 looseBalance = want.balanceOf(address(this));
        uint256 total = balanceUnderlying.add(looseBalance);

        if (amount > total) {
            //cant withdraw more than we own
            amount = total;
        }

        if (looseBalance >= amount) {
            want.safeTransfer(address(strategy), amount);
            return amount;
        }

        //not state changing but OK because of previous call
        uint256 liquidity = want.balanceOf(address(aToken));

        if (liquidity > 1) {
            uint256 toWithdraw = amount.sub(looseBalance);

            if (toWithdraw <= liquidity) {
                //we can take all
                _lendingPool().withdraw(address(want), toWithdraw, address(this));
            } else {
                //take all we can
                _lendingPool().withdraw(address(want), liquidity, address(this));
            }
        }
        looseBalance = want.balanceOf(address(this));
        want.safeTransfer(address(strategy), looseBalance);
        return looseBalance;
    }

    function _deposit(uint256 amount) internal {
        ILendingPool lp = _lendingPool();
        // NOTE: check if allowance is enough and acts accordingly
        // allowance might not be enough if
        //     i) initial allowance has been used (should take years)
        //     ii) lendingPool contract address has changed (Sturdy updated the contract address)
        if (want.allowance(address(this), address(lp)) < amount) {
            IERC20(address(want)).safeApprove(address(lp), 0);
            IERC20(address(want)).safeApprove(address(lp), type(uint256).max);
        }

        uint16 referral;
        uint16 _customReferral = customReferral;
        if (_customReferral != 0) {
            referral = _customReferral;
        }

        lp.deposit(address(want), amount, address(this), referral);
    }

    function _lendingPool() internal view returns (ILendingPool lendingPool) {
        lendingPool = ILendingPool(protocolDataProvider.ADDRESSES_PROVIDER().getLendingPool());
    }

    function _oracle() internal view returns (IPriceOracle oracle) {
        oracle = IPriceOracle(protocolDataProvider.ADDRESSES_PROVIDER().getPriceOracle());
    }

    function _getTotalBorrowableLiquidityInPrice() internal view returns (uint256) {
        uint256 totalBorrowableLiquidityInPrice;
        address[] memory reserves = _lendingPool().getReservesList();
        uint256 reserveCount = reserves.length;

        for (uint256 i; i < reserveCount; ++i) {
            (uint256 decimals, , , , , , bool borrowingEnabled, , , ) = protocolDataProvider.getReserveConfigurationData(reserves[i]);
            if (!borrowingEnabled) continue;

            (
                uint256 availableLiquidity,
                uint256 totalStableDebt,
                uint256 totalVariableDebt,
                ,
                ,
                ,
                ,
                ,
                ,

            ) = protocolDataProvider.getReserveData(reserves[i]);
            totalBorrowableLiquidityInPrice = totalBorrowableLiquidityInPrice.add(
                availableLiquidity
                    .add(totalStableDebt)
                    .add(totalVariableDebt)
                    .mul(_oracle().getAssetPrice(reserves[i]))
                    .div(10**decimals)
            );
        }

        return totalBorrowableLiquidityInPrice;
    }

    function _getLiquidityRateAfterDeposit(uint256 extraAmount) internal view returns (uint256) {
        DataTypes.ReserveData memory reserveData = _lendingPool().getReserveData(address(want));
        (uint256 decimals, , , , uint256 reserveFactor, , , , , ) = protocolDataProvider.getReserveConfigurationData(address(want));

        (
            uint256 availableLiquidity,
            uint256 totalStableDebt,
            uint256 totalVariableDebt,
            ,
            ,
            ,
            uint256 averageStableBorrowRate,
            ,
            ,

        ) = protocolDataProvider.getReserveData(address(want));

        (uint256 newLiquidityRate, , ) = IReserveInterestRateStrategy(reserveData.interestRateStrategyAddress).calculateInterestRates(
            address(want),
            availableLiquidity.add(extraAmount),
            totalStableDebt,
            totalVariableDebt,
            averageStableBorrowRate,
            reserveFactor
        );

        return newLiquidityRate;
    }

    function protectedTokens() internal view override returns (address[] memory) {
        address[] memory protected = new address[](2);
        protected[0] = address(want);
        protected[1] = address(aToken);
        return protected;
    }

    modifier keepers() {
        require(
            msg.sender == address(keep3r) ||
                msg.sender == address(strategy) ||
                msg.sender == vault.governance() ||
                msg.sender == IBaseStrategy(strategy).management(),
            "!keepers"
        );
        _;
    }
}
