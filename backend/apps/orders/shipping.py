# apps/orders/shipping.py

# Cidades com frete grátis
FREE_SHIPPING_CITIES = ['uberlândia', 'araguari']

# Frete por estado (UF → valor)
SHIPPING_TABLE = {
    'MG': 12.00,
    'SP': 15.00,
    'RJ': 18.00,
    'PR': 20.00,
    'SC': 20.00,
    'RS': 20.00,
}
SHIPPING_NORTH_NORTHEAST = 30.00

NORTH_NORTHEAST_STATES = [
    'AC','AL','AM','AP','BA','CE','MA',
    'PA','PB','PE','PI','RN','RO','RR','SE','TO'
]

def calculate_shipping(state: str, city: str) -> float:
    """
    Retorna o valor do frete com base no estado e cidade.
    """
    city_normalized  = city.strip().lower()
    state_normalized = state.strip().upper()

    # Frete grátis para cidades especiais
    if city_normalized in FREE_SHIPPING_CITIES:
        return 0.00

    # Sul
    if state_normalized in ['PR', 'SC', 'RS']:
        return SHIPPING_TABLE.get(state_normalized, 20.00)

    # Norte / Nordeste
    if state_normalized in NORTH_NORTHEAST_STATES:
        return SHIPPING_NORTH_NORTHEAST

    # Tabela padrão (MG, SP, RJ, etc.)
    return SHIPPING_TABLE.get(state_normalized, 25.00)  # 25 = outros estados não mapeados
