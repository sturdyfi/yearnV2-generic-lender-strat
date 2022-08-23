import brownie
import requests
from brownie.network.state import Chain

def deposit(amount, user, currency, vault):
    # print('\n----user deposits----')
    currency.approve(vault, amount, {"from": user})
    # print('deposit amount:', amount.to('ether'))
    vault.deposit(amount, {"from": user})


def sleep(chain, blocks):
    timeN = chain.time()
    endTime = blocks * 13 + timeN
    chain.mine(blocks, endTime)

#Determines if second is with 1% of first
#For apr calcs
def close(first, second):
    if first * 1.01 >= second or first * .99 <= second:
        return True
    else:
        return False
