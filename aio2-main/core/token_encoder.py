"""
トークン数エンコーダー（32進数変換）

ユーザーに実際のトークン数を隠すため、32進数に変換して表示
"""


def encode_token_count(count: int) -> str:
    """
    トークン数を32進数文字列に変換
    
    Args:
        count: トークン数
    
    Returns:
        32進数文字列（大文字）
    """
    if count < 0:
        return "-" + _to_base32(-count)
    return _to_base32(count)


def decode_token_count(encoded: str) -> int:
    """
    32進数文字列をトークン数に復号
    
    Args:
        encoded: 32進数文字列
    
    Returns:
        元のトークン数
    """
    if encoded.startswith("-"):
        return -_from_base32(encoded[1:])
    return _from_base32(encoded)


BASE32_ALPHABET = "0123456789ABCDEFGHJKLMNPQRSTUVWX"  # 32文字（I/O除外）
BASE32_RADIX = 32


def _to_base32(num: int) -> str:
    """数値を32進数に変換"""
    if num == 0:
        return "0"
    
    result = []
    
    while num > 0:
        result.append(BASE32_ALPHABET[num % BASE32_RADIX])
        num //= BASE32_RADIX
    
    return "".join(reversed(result))


def _from_base32(encoded: str) -> int:
    """32進数文字列を数値に変換"""
    result = 0
    
    for char in encoded.upper():
        if char not in BASE32_ALPHABET:
            raise ValueError(f"無効な文字: {char}")
        result = result * BASE32_RADIX + BASE32_ALPHABET.index(char)
    
    return result


def encode_cost(cost: float, precision: int = 2) -> str:
    """
    コストを32進数に変換（小数点対応）
    
    Args:
        cost: コスト（USD/JPY）
        precision: 小数点以下の桁数
    
    Returns:
        32進数文字列（整数部分と小数部分を分離）
    """
    # 小数点を考慮して整数に変換
    multiplier = 10 ** precision
    integer_cost = int(cost * multiplier)
    
    # 符号を保持
    sign = "-" if integer_cost < 0 else ""
    integer_cost = abs(integer_cost)
    
    return sign + _to_base32(integer_cost)


def decode_cost(encoded: str, precision: int = 2) -> float:
    """
    32進数文字列をコストに復号
    
    Args:
        encoded: 32進数文字列
        precision: 小数点以下の桁数
    
    Returns:
        元のコスト
    """
    sign = -1 if encoded.startswith("-") else 1
    encoded = encoded.lstrip("-")
    
    integer_cost = _from_base32(encoded)
    return sign * (integer_cost / (10 ** precision))


def format_encoded_tokens(input_tokens: int, output_tokens: int) -> str:
    """
    トークン数をエンコードして表示用文字列に整形
    
    Args:
        input_tokens: 入力トークン数
        output_tokens: 出力トークン数
    
    Returns:
        エンコード済み表示文字列
    """
    input_encoded = encode_token_count(input_tokens)
    output_encoded = encode_token_count(output_tokens)
    
    # 表記を分かりにくくするため、入力=n、出力=o とする
    return f"n: {input_encoded} / o: {output_encoded}"


def format_encoded_cost(cost_jpy: float, cost_usd: float) -> str:
    """
    コストをエンコードして表示用文字列に整形
    
    Args:
        cost_jpy: JPYコスト
        cost_usd: USDコスト
    
    Returns:
        エンコード済み表示文字列
    """
    jpy_encoded = encode_cost(cost_jpy)
    usd_encoded = encode_cost(cost_usd, precision=6)
    
    return f"JPY: {jpy_encoded} / USD: {usd_encoded}"
