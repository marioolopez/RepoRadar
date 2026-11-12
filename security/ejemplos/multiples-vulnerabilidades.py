#ARCHIVO DE PRUEBA: NO EJECUTAR
import pickle
import subprocess


def ejemplo_eval(texto):
    return eval(texto)


def ejemplo_exec(codigo):
    exec(codigo)


def ejemplo_subprocess(comando):
    subprocess.run(comando, shell=True)


def ejemplo_pickle(archivo):
    with open(archivo, "rb") as fichero:
        return pickle.load(fichero)



#este archivo es únicamente para analizarlo estáticamente. No debes ejecutarlo