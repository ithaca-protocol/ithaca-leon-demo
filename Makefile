include .env
export



FUNDLOCK=0x4A906f90db434d51898FD10bCBa7615Aa5BF45e7
WETH=0xbf4864f3d55bbefc14f2fd4af8217184e6b6168b
USDC=0x75faf114eafb1BDbe2F0316DF893fd58CE46AA4d
WBTC=0x28c4a772af0286ab0dcf60075128a1e8e42fe53a

balance:
	@echo "Wallet" ${WALLET}

	@echo -n "ETH balance: "
	@cast balance ${WALLET} --rpc-url ${RPC_URL} | xargs -I '{}' echo "scale=4; {} / 10^18 " | bc

	@echo -n "USDC balance: "
	@cast call ${USDC} "balanceOf(address)(uint256)" ${WALLET} --rpc-url ${RPC_URL} | awk '{print $$1}' | xargs -I '{}' echo "scale=4; {} / 1000000" | bc

	@echo -n "WETH balance: "
	@cast call ${WETH} "balanceOf(address)(uint256)" ${WALLET} --rpc-url ${RPC_URL} | awk '{print $$1}' | xargs -I '{}' echo "scale=4; {} / 10^18" | bc

	@echo -n "WBTC balance: "
	@cast call ${WBTC} "balanceOf(address)(uint256)" ${WALLET} --rpc-url ${RPC_URL} | awk '{print $$1}' | xargs -I '{}' echo "scale=4; {} / 10^18" | bc

deposit:
	@cast send ${WBTC} "approve(address,uint256)" ${FUNDLOCK} 10000000ether --rpc-url ${RPC_URL} --private-key ${PRIVATE_KEY}
	@cast send ${FUNDLOCK} "deposit(address,address,uint256)" ${WALLET} ${WBTC} 9ether --rpc-url ${RPC_URL} --private-key ${PRIVATE_KEY}


mint:
	@cast send ${USDC} "mint(address,uint256)" ${WALLET} 10000000ether --rpc-url ${RPC_URL} --private-key ${PRIVATE_KEY}
	@cast send ${WETH} "mint(address,uint256)" ${WALLET} 10000000ether --rpc-url ${RPC_URL} --private-key ${PRIVATE_KEY}
