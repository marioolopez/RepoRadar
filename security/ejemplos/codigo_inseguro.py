#Archivo de prueba para aprender a detectar problemas de seguridad

def calcular_expresion(expresion):
    #eval() ejecuta expresiones de Python.
    #es peligroso utilizarlo con datos no confiables.
    resultado = eval(expresion)
    return resultado