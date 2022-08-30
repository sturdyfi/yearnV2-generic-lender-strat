// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.6.12;

interface ISturdyAPRDataProvider {
    function APR(address _borrowReserve, bool _not_real) external view returns (uint256);
}