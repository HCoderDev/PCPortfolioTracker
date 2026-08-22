def format_inr_commas(val: float) -> str:
    """Format double value in Indian numbering format: 12,34,567.89"""
    if val is None:
        return "0.00"
    
    is_negative = val < 0
    val = abs(val)
    
    s = f"{val:.2f}"
    parts = s.split(".")
    integer_part = parts[0]
    decimal_part = parts[1]
    
    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last3 = integer_part[-3:]
        rest = integer_part[:-3]
        
        # Split rest into 2-digit chunks from right
        chunks = []
        while len(rest) > 2:
            chunks.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            chunks.insert(0, rest)
        
        formatted_int = ",".join(chunks) + "," + last3
        
    result = f"{formatted_int}.{decimal_part}"
    return f"-{result}" if is_negative else result

def format_currency(val: float, currency_code: str = "INR") -> str:
    if val is None:
        val = 0.0
    symbol = "₹" if currency_code == "INR" else "$" if currency_code == "USD" else f"{currency_code} "
    formatted_num = format_inr_commas(val) if currency_code == "INR" else f"{val:,.2f}"
    return f"{symbol}{formatted_num}"

def format_percent(val: float, decimals: int = 2) -> str:
    if val is None:
        return "0.00%"
    sign = "+" if val > 0 else ""
    return f"{sign}{val:.{decimals}f}%"

def format_number(val: float, decimals: int = 2) -> str:
    if val is None:
        return "0.00"
    return f"{val:,.{decimals}f}"
