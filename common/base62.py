"""Codificación base62 de ids enteros.

Usa el mismo alfabeto que pybase62 (0-9, A-Z, a-z), así que los resultados
son equivalentes si alguien del grupo prefiere usar esa librería.
"""

ALFABETO = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALFABETO)  # 62
_INDICE = {c: i for i, c in enumerate(ALFABETO)}


def encode(numero: int) -> str:
    """Convierte un entero no negativo a su representación base62."""
    if numero < 0:
        raise ValueError("El número debe ser no negativo")
    if numero == 0:
        return ALFABETO[0]
    digitos = []
    while numero > 0:
        numero, resto = divmod(numero, BASE)
        digitos.append(ALFABETO[resto])
    return "".join(reversed(digitos))


def decode(texto: str) -> int:
    """Convierte un string base62 de vuelta a entero."""
    if not texto:
        raise ValueError("El texto no puede estar vacío")
    numero = 0
    for c in texto:
        if c not in _INDICE:
            raise ValueError(f"Carácter inválido para base62: {c!r}")
        numero = numero * BASE + _INDICE[c]
    return numero
