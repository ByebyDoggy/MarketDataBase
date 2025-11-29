TOP_SPOT_EXCHANGES = ['okex', 'bybit_spot', 'binance', 'gate', 'bitget', 'mxc']

TOP_SWAP_EXCHANGES = ['binance_futures', 'bitget_futures', 'gate_futures', 'bybit',
                      'mxc_futures', 'okex_swap']

UPDATE_HOLDERS_EXCHANGES = ['binance','binance_futures','okex','okex_swap']

CMC_SPOT_EXCHANGE_TO_CCXT_EXCHANGE: dict[str, str] = {
    'okex': 'okx',
    'bybit_spot': 'bybit',
    'binance': 'binance',
    'gate': 'gateio',
    'bitget': 'bitget',
    'mxc': 'mxc',
}
CCXT_SPOT_EXCHANGE_TO_CMC_EXCHANGE: dict[str, str] = {
    'okx': 'okex',
    'bybit': 'bybit_spot',
    'binance': 'binance',
    'gateio': 'gate',
    'bitget': 'bitget',
    'mxc': 'mxc',
}
CCXT_SWAP_EXCHANGE_TO_CMC_EXCHANGE: dict[str, str] = {
    'binance': 'binance_futures',
    'bitget': 'bitget_futures',
    'gateio': 'gate_futures',
    'bybit': 'bybit',
    'mxc': 'mxc_futures',
    'okx': 'okex_swap',
}



CMC_SWAP_EXCHANGE_TO_CCXT_EXCHANGE: dict[str, str] = {
    'binance_futures': 'binance',
    'bitget_futures': 'bitget',
    'gate_futures': 'gateio',
    'bybit': 'bybit',
    'mxc_futures': 'mxc',
    'okex_swap': 'okex',
}

WRAPPED_TOKEN_ORIGIN_TOKEN_ID_MAP: dict[str, str] = {
    'weth': 'ethereum',
    'stakewise-v3-oseth': 'ethereum',
    'wrapped-steth': 'ethereum',
    'wrapped-bitcoin': 'bitcoin',
    'staked-ether': 'ethereum',
    'mantle-staked-ether': 'ethereum',
    'mantle-restaked-eth': 'ethereum',
    'bridged-wbnb': 'binancecoin',
    'wbnb': 'binancecoin',
}

ORIGIN_TOKEN_WRAPPED_TOKEN_MAP: dict[str, list[str]] = {
    'ethereum': ['weth', 'stakewise-v3-oseth', 'wrapped-steth', 'staked-ether', 'mantle-staked-ether', 'mantle-restaked-eth'],
    'bitcoin': ['wrapped-bitcoin'],
    "binancecoin":['bridged-wbnb','wbnb']
}
