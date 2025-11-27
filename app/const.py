TOP_SPOT_EXCHANGES = ['okex', 'bybit_spot', 'binance', 'gate', 'bitget', 'mxc']

TOP_SWAP_EXCHANGES = ['binance_futures', 'bitget_futures', 'gate_futures', 'bybit',
                      'mxc_futures', 'okex_swap']

UPDATE_HOLDERS_EXCHANGES = ['binance','binance_futures','okex','okex_swap']

WRAPPED_TOKEN_ORIGIN_TOKEN_ID_MAP: dict[str, str] = {
    'weth': 'ethereum',
    'stakewise-v3-oseth': 'ethereum',
    'wrapped-steth': 'ethereum',
    'wrapped-bitcoin': 'bitcoin',
    'staked-ether': 'ethereum',
    'mantle-staked-ether': 'ethereum',
    'mantle-restaked-eth': 'ethereum',

}

ORIGIN_TOKEN_WRAPPED_TOKEN_MAP: dict[str, list[str]] = {
    'ethereum': ['weth', 'stakewise-v3-oseth', 'wrapped-steth', 'staked-ether', 'mantle-staked-ether', 'mantle-restaked-eth'],
    'bitcoin': ['wrapped-bitcoin']
}
