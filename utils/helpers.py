def gerar_avatar(nome):

    if not nome:
        return "CI"

    partes = nome.split()

    if len(partes) == 1:
        return partes[0][:2].upper()

    return (partes[0][0] + partes[1][0]).upper()
