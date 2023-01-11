# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/updates.ipynb.

# %% auto 0
__all__ = ['connect_db', 'clean_mosaico', 'update_radcom', 'update_stel', 'update_mosaico', 'update_telecom', 'valida_coords',
           'update_base']

# %% ../nbs/updates.ipynb 2
from decimal import Decimal, getcontext
from typing import Union
import gc

import pandas as pd
import pyodbc
from rich.console import Console
from pyarrow import ArrowInvalid, ArrowTypeError
from fastcore.xtras import Path
from fastcore.foundation import L
from tqdm.auto import tqdm
import pyodbc
from pymongo import MongoClient
from dotenv import load_dotenv

from .constants import *
from .format import parse_bw

getcontext().prec = 5
load_dotenv()

# %% ../nbs/updates.ipynb 4
def connect_db(
    server: str = "ANATELBDRO05",  # Servidor do Banco de Dados
    database: str = "SITARWEB",  # Nome do Banco de Dados
    trusted_conn: str = "yes",  # Conexão Segura: yes | no
    mult_results: bool = True,  # Múltiplos Resultados
) -> pyodbc.Connection:
    """Conecta ao Banco `server` e retorna o 'cursor' (iterador) do Banco"""
    return pyodbc.connect(
        "Driver={ODBC Driver 17 for SQL Server};"
        f"Server={server};"
        f"Database={database};"
        f"Trusted_Connection={trusted_conn};"
        f"MultipleActiveResultSets={mult_results};",
        timeout=TIMEOUT,
    )

# %% ../nbs/updates.ipynb 7
def clean_mosaico(
    df: pd.DataFrame,  # DataFrame com os dados de Estações e Plano_Básico mesclados
    pasta: Union[
        str, Path
    ],  # Pasta com os dados de municípios para imputar coordenadas ausentes
) -> pd.DataFrame:  # DataFrame com os dados mesclados e limpos
    """Clean the merged dataframe with the data from the MOSAICO page"""
    # df = input_coordenates(df, pasta) # TODO: Implementar função de verificação de coordenadas diretamente no arquivo final base e eliminar essa chamada
    df = df[
        df.Status.str.contains("-C1$|-C2$|-C3$|-C4$|-C7|-C98$", na=False)
    ].reset_index(drop=True)
    for c in df.columns:
        df.loc[df[c] == "", c] = pd.NA
    df.loc["Frequência"] = df.Frequência.astype("str").str.replace(",", ".")
    df = df[df.Frequência.notna()].reset_index(drop=True)
    df.loc["Frequência"] = df.Frequência.astype("float")
    df.loc[df.Num_Serviço == "205", "Frequência"] = df.loc[
        df.Num_Serviço == "205", "Frequência"
    ].apply(lambda x: Decimal(x) / Decimal(1000))
    df.loc[:, "Validade_RF"] = df.Validade_RF.astype("string").str.slice(0, 10)
    return df[df.Código_Município.notna()].reset_index(drop=True)

# %% ../nbs/updates.ipynb 9
def _save_df(df: pd.DataFrame, folder: Union[str, Path], stem: str) -> pd.DataFrame:
    """Format, Save and return a dataframe"""
    for c in df.columns:
        df[c] = df[c].astype("string").str.lstrip().str.rstrip()
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    if "Código_Município" in df:
        df = df[df.Código_Município.notna()].reset_index(drop=True)
    try:
        file = Path(f"{folder}/{stem}.parquet.gzip")
        df.to_parquet(file, compression="gzip", index=False)
    except (ArrowInvalid, ArrowTypeError):
        file.unlink(missing_ok=True)
        try:
            file = Path(f"{folder}/{stem}.xlsx")
            with pd.ExcelWriter(file) as wb:
                df.to_excel(wb, sheet_name="DataBase", engine="openpyxl", index=False)
        except Exception as e:
            raise ValueError(f"Could not save {stem} to {file}") from e
    return df

# %% ../nbs/updates.ipynb 10
def update_radcom(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Atualiza a tabela local retornada pela query `RADCOM`, com tratamento de erro de conectividade."""
    console = Console()
    with console.status(
        "[cyan]Lendo o Banco de Dados de Radcom...", spinner="earth"
    ) as status:
        try:
            return _extract_radcom(conn, folder)
        except pyodbc.OperationalError as e:
            status.console.log(
                "Não foi possível abrir uma conexão com o SQL Server. Esta conexão somente funciona da rede cabeada!"
            )
            raise ConnectionError from e


def _extract_radcom(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    df = pd.read_sql_query(SQL_RADCOM, conn)
    df["Entidade"] = df.Entidade.str.rstrip().str.lstrip()
    df["Num_Serviço"] = "231"
    df["Classe_Emissão"] = pd.NA
    df["Largura_Emissão(kHz)"] = "256"
    df["Validade_RF"] = pd.NA
    df["Status"] = "RADCOM"
    df["Fonte"] = "SRD"
    df["Multiplicidade"] = "1"
    a = df.Situação.isna()
    df.loc[a, "Classe"] = df.loc[a, "Fase"]
    df.loc[~a, "Classe"] = (
        df.loc[~a, "Fase"].astype("string")
        + "-"
        + df.loc[~a, "Situação"].astype("string")
    )
    df.drop(["Fase", "Situação"], axis=1, inplace=True)
    df = df.loc[:, COLUNAS]
    return _save_df(df, folder, "radcom")

# %% ../nbs/updates.ipynb 13
def update_stel(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Atualiza a tabela local retornada pela query `STEL`, com tratamento de erro de conectividade."""
    console = Console()
    with console.status(
        "[red]Lendo o Banco de Dados do STEL",
        spinner="bouncingBall",
    ) as status:
        try:
            return _extract_stel(conn, folder)
        except pyodbc.OperationalError as e:
            status.console.log(
                "Não foi possível abrir uma conexão com o SQL Server. Esta conexão somente funciona da rede cabeada!"
            )
            raise ConnectionError from e


def _extract_stel(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Atualiza a tabela local retornada pela query `STEL`"""
    stel = pd.read_sql_query(SQL_STEL, conn)
    stel["Status"] = "L"
    stel["Entidade"] = stel.Entidade.str.rstrip().str.lstrip()
    stel["Fonte"] = "STEL"
    stel.loc[:, ["Largura_Emissão(kHz)", "_"]] = (
        stel.Largura_Emissão.fillna("").apply(parse_bw).tolist()
    )
    stel.drop(["Largura_Emissão", "_"], axis=1, inplace=True)
    stel.loc[:, "Validade_RF"] = stel.Validade_RF.astype("string").str.slice(0, 10)
    stel.loc[stel.Unidade == "kHz", "Frequência"] = stel.loc[
        stel.Unidade == "kHz", "Frequência"
    ].apply(lambda x: Decimal(x) / Decimal(1000))
    stel.loc[stel.Unidade == "GHz", "Frequência"] = stel.loc[
        stel.Unidade == "GHz", "Frequência"
    ].apply(lambda x: Decimal(x) * Decimal(1000))
    stel.drop("Unidade", axis=1, inplace=True)
    stel["Multiplicidade"] = 1
    stel = stel.loc[:, COLUNAS]
    return _save_df(stel, folder, "stel")

# %% ../nbs/updates.ipynb 15
def update_mosaico(
    mongo_client: MongoClient,  # Objeto de conexão com o MongoDB
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Efetua a query na tabela de Radiodifusão no banco mongoDB `mongo_client` e atualiza o arquivo local"""
    console = Console()
    with console.status(
        "Consolidando os dados do Mosaico...", spinner="clock"
    ) as status:

        database = mongo_client["sms"]
        collection = database["srd"]
        list_data = list(collection.find(MONGO_SRD, projection=COLS_SRD.keys()))
        mosaico = pd.json_normalize(list_data)
        mosaico = mosaico.drop(columns=["estacao"])
        mosaico = mosaico[list(COLS_SRD.keys())]
        mosaico.rename(COLS_SRD, axis=1, inplace=True)
        mosaico = clean_mosaico(mosaico, folder)
        mosaico["Fonte"] = "MOS"
        mosaico.loc[:, ["Largura_Emissão(kHz)", "Classe_Emissão"]] = (
            mosaico.Num_Serviço.astype("string").map(BW_MAP).apply(parse_bw).tolist()
        )
        mosaico.loc[mosaico.Classe_Emissão == "", "Classe_Emissão"] = pd.NA
        mosaico["Multiplicidade"] = 1
        mosaico = mosaico.loc[:, COLUNAS]
    return _save_df(mosaico, folder, "mosaico")

# %% ../nbs/updates.ipynb 18
def update_telecom(
    mongo_client: MongoClient,  # Objeto de conexão com o MongoDB
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Efetua a query na tabela `licenciamento` no banco mongoDB `mongo_client` e atualiza o arquivo local"""

    console = Console()
    console.print(
        "[red]Lendo o Banco de Dados de Licenciamento do Mosaico. Processo Lento, aguarde..."
    )
    database = mongo_client["sms"]
    collection = database["licenciamento"]
    c = collection.find(MONGO_TELECOM, projection={k: 1.0 for k in COLS_TELECOM.keys()})
    result = L()
    for doc in tqdm(c):
        result.append(doc)
    df = pd.json_normalize(result)
    df.drop("_id", axis=1, inplace=True)
    df.rename(COLS_TELECOM, axis=1, inplace=True)
    df["Designacao_Emissão"] = df.Designacao_Emissão.str.replace(",", " ")
    df["Designacao_Emissão"] = (
        df.Designacao_Emissão.str.strip().str.lstrip().str.rstrip().str.upper()
    )
    df["Designacao_Emissão"] = df.Designacao_Emissão.str.split(" ")
    df = df.explode("Designacao_Emissão")
    df.loc[df.Designacao_Emissão == "/", "Designacao_Emissão"] = ""
    df.loc[:, ["Largura_Emissão(kHz)", "Classe_Emissão"]] = df.Designacao_Emissão.apply(
        parse_bw
    ).tolist()
    df.drop("Designacao_Emissão", axis=1, inplace=True)
    _save_df(df, folder, "telecom_raw")
    subset = [
        "Entidade",
        "Longitude",
        "Latitude",
        "Classe",
        "Frequência",
        "Num_Serviço",
        "Largura_Emissão(kHz)",
        "Classe_Emissão",
    ]
    df.dropna(subset=subset, axis=0, inplace=True)
    df_sub = (
        df[~df.duplicated(subset=subset, keep="first")].reset_index(drop=True).copy()
    )
    # df_sub = df_sub.set_index(subset).sort_index()
    df_sub["Multiplicidade"] = (
        df.groupby(subset, sort=False).count()["Número_Estação"]
    ).tolist()
    df_sub["Status"] = "L"
    df_sub["Fonte"] = "MOS"
    del df
    gc.collect()
    df_sub = df_sub.reset_index()
    df_sub = df_sub.loc[:, COLUNAS]
    return _save_df(df_sub, folder, "telecom")

# %% ../nbs/updates.ipynb 20
def valida_coords(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    row: pd.Series,  # Linha de um DataFrame
) -> tuple:  # DataFrame com dados do município
    """Valida os dados de coordenadas e município em `row` no polígono dos municípios em banco corporativo"""

    sql = SQL_VALIDA_COORD.format(
        row["Longitude"], row["Latitude"], row["Código_Município"]
    )
    crsr = conn.cursor()
    crsr.execute(sql)
    result = crsr.fetchone()
    if result is None:
        return (row["Município"], row["Longitude"], row["Latitude"], "-1")
    elif result.COORD_VALIDA == 1:
        return result
    else:
        return (
            result.NO_MUNICIPIO,
            result.NU_LONGITUDE,
            result.NU_LATITUDE,
            result.COORD_VALIDA,
        )

# %% ../nbs/updates.ipynb 21
def update_base(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    clientMongoDB: MongoClient,  # Ojeto de conexão com o MongoDB
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    # sourcery skip: use-fstring-for-concatenation
    """Wrapper que atualiza opcionalmente lê e atualiza as 4 bases indicadas anteriormente, as combina e salva o arquivo consolidado na folder `folder`"""
    stel = update_stel(
        conn,
        folder,
    )
    radcom = update_radcom(conn, folder)
    mosaico = update_mosaico(clientMongoDB, folder)
    telecom = update_telecom(clientMongoDB, folder)

    rd = (
        pd.concat([mosaico, radcom, stel, telecom])
        .sort_values(["Frequência", "Latitude", "Longitude"])
        .reset_index(drop=True)
    )
    rd.loc[:, ["Latitude", "Longitude"]] = rd.loc[:, ["Latitude", "Longitude"]].fillna(
        "-1"
    )  # Validando Coordenadas
    rd["Coords_Valida"] = pd.NA
    rd[["Município", "Longitude", "Latitude", "Coords_Valida"]] = rd.apply(
        lambda row: pd.Series(list(valida_coords(conn, row))), axis=1
    )
    rd = rd.drop(rd[rd.Coords_Valida == "-1"].index)
    return _save_df(rd, folder, "base")
