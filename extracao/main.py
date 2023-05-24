# AUTOGENERATED! DO NOT EDIT! File to edit: ..\nbs\main.ipynb.

# %% auto 0
__all__ = ['LIMIT_FREQ', 'get_db']

# %% ..\nbs\main.ipynb 3
import os
from pathlib import Path
import json
from typing import Union
from datetime import datetime

import pandas as pd
from fastcore.test import *
from rich import print
import pyodbc
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv

from .constants import APP_ANALISE_PT, APP_ANALISE_EN
from .reading import read_base, read_aero
from .format import merge_close_rows


# %% ..\nbs\main.ipynb 4
LIMIT_FREQ = 84812.50
load_dotenv(find_dotenv())

# %% ..\nbs\main.ipynb 5
def _filter_matlab(
    df: pd.DataFrame,  # Arquivo de Dados Base de Entrada
) -> pd.DataFrame:  # Arquivo de Dados formatado para leitura no Matlab
    """Recebe a base de dados da Anatel e formata as colunas para leitura de acordo com os requisitos do Matlab"""
    df["#Estação"] = df["Número_Estação"]
    df.loc[df.Multiplicidade != "1", "#Estação"] = (
        df.loc[df.Multiplicidade != "1", "Número_Estação"]
        + "+"
        + df.loc[df.Multiplicidade != "1", "Multiplicidade"]
    )
    cols_desc = [
        "Fonte",
        "Status",
        "Classe",
        "Entidade",
        "Fistel",
        "#Estação",
        "Município_IBGE",
        "UF",
    ]
    df.loc[:, cols_desc].fillna("NI", inplace=True)

    df["Descrição"] = (
        "["
        + df.Fonte
        + "] "
        + df.Status
        + ", "
        + df.Classe
        + ", "
        + df.Entidade.str.title()
        + " ("
        + df.Fistel
        + ", "
        + df["#Estação"]
        + "), "
        + df.Município_IBGE
        + "/"
        + df.UF
    )

    bad_coords = df.Coords_Valida_IBGE == "0"

    df.loc[bad_coords == "False", "Descrição"] = (
        df.loc[bad_coords == "False", "Descrição"] + "*"
    )

    df.loc[bad_coords, ["Latitude", "Longitude"]] = df.loc[
        bad_coords, ["Latitude_IBGE", "Longitude_IBGE"]
    ].values

    df = df.loc[:, APP_ANALISE_PT]
    df.columns = APP_ANALISE_EN
    return df


def _format_matlab(
    df: pd.DataFrame,  # Arquivo de Dados Base de Entrada
) -> pd.DataFrame:  # Arquivo de Dados formatado para leitura no Matlab
    """Formata o arquivo final de dados para o formato esperado pela aplicação em Matlab"""
    for c in ["Latitude", "Longitude"]:
        df.loc[:, c] = df.loc[:, c].fillna(-1).astype("float32")
    df["Frequency"] = df["Frequency"].astype("float64")
    df.loc[df.Service.isin(["", "-1"]), "Service"] = pd.NA
    df["Service"] = df.Service.fillna("-1").astype("int16")
    df.loc[df.Station.isin(["", "-1"]), "Station"] = pd.NA
    df["Station"] = df.Station.fillna("-1").astype("int32")
    df.loc[df.BW.isin(["", "-1"]), "BW"] = pd.NA
    df["BW"] = df["BW"].astype("float32").fillna(-1)
    df.loc[df["Class"].isin(["", "-1"]), "Class"] = pd.NA
    df["Class"] = df.Class.fillna("NI").astype("category")
    df = (
        df.drop_duplicates(keep="first")
        .sort_values(by=["Frequency", "Latitude", "Longitude"])
        .reset_index(drop=True)
    )
    df["Id"] = [f"#{i+1}" for i in df.index]
    df["Id"] = df.Id.astype("string")
    df.loc[df.Description == "", "Description"] = pd.NA
    df["Description"] = df["Description"].astype("string").fillna("NI")
    df = df[df.Frequency <= LIMIT_FREQ]
    return df[["Id"] + list(APP_ANALISE_EN)]


# %% ..\nbs\main.ipynb 6
def get_db(
    path: Union[str, Path],  # Pasta onde salvar os arquivos",
    connSQL: pyodbc.Connection = None,  # Objeto de conexão do banco SQL Server
    clientMongoDB: MongoClient = None,  # Objeto de conexão do banco MongoDB
) -> pd.DataFrame:  # Retorna o DataFrame com as bases da Anatel e da Aeronáutica
    """Lê e opcionalmente atualiza as bases da Anatel, mescla as bases da Aeronáutica, salva e retorna o arquivo
    A atualização junto às bases de dados da Anatel é efetuada caso ambos objetos de banco `connSQL` e `clientMongoDB` forem válidos`
    """
    dest = Path(path)
    dest.mkdir(parents=True, exist_ok=True)
    print(":scroll:[green]Lendo as bases de dados da Anatel...")
    df = read_base(path, connSQL, clientMongoDB)
    df = _filter_matlab(df)
    mod_times = {"ANATEL": datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
    print(":airplane:[blue]Requisitando os dados da Aeronáutica.")
    update = all([connSQL, clientMongoDB])
    aero = read_aero(path, update=update)
    mod_times["AERONAUTICA"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(":spoon:[yellow]Mesclando os dados da Aeronáutica.")
    df = merge_close_rows(df, aero)
    df.loc[len(df), :] =  [-1,  -15.7801,  -47.9292, "[TEMP] L, FX, Estação do SMP licenciada (cadastro temporário)", "10", "999999999", 'NI', "-1"] #Paliativo...
    df = _format_matlab(df)
    print(":card_file_box:[green]Salvando os arquivos...")
    df.to_parquet(f"{dest}/AnatelDB.parquet.gzip", compression="gzip", index=False)
    versiondb = json.loads((dest / "VersionFile.json").read_text())
    mod_times["ReleaseDate"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    versiondb["anateldb"].update(mod_times)
    json.dump(versiondb, (dest / "VersionFile.json").open("w"))
    print("Sucesso :zap:")
    return df
