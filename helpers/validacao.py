def verificar_campos_obrigatorios(*, obrigatorios: list, body: dict):
    for obrigatorio in obrigatorios:
        valor = body.get(obrigatorio.lower(), None)
        if not valor:
            return False
    return True