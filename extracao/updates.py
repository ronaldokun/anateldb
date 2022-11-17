# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/updates.ipynb.

# %% auto 0
__all__ = ['connect_db', 'clean_mosaico', 'update_radcom', 'update_stel', 'update_mosaico', 'update_telecom', 'valida_coord',
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
from fastcore.test import test_eq
from fastcore.foundation import L
from tqdm.auto import tqdm
import pyodbc
from pymongo import MongoClient

from .constants import *
from .format import parse_bw, format_types, input_coordenates

getcontext().prec = 5

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

# %% ../nbs/updates.ipynb 6
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
    df.loc["Frequência"] = df.Frequência.str.replace(",", ".")
    df = df[df.Frequência.notna()].reset_index(drop=True)
    df.loc["Frequência"] = df.Frequência.astype("float")
    df.loc[df.Num_Serviço == "205", "Frequência"] = df.loc[
        df.Num_Serviço == "205", "Frequência"
    ].apply(lambda x: Decimal(x) / Decimal(1000))
    df.loc[:, "Validade_RF"] = df.Validade_RF.astype("string").str.slice(0, 10)
    return df

# %% ../nbs/updates.ipynb 8
def _save_df(df: pd.DataFrame, folder: Union[str, Path], stem: str) -> pd.DataFrame:
    """Format, Save and return a dataframe"""
    df = format_types(df, stem)
    df = df.dropna(subset=["Latitude", "Longitude"]).reset_index(drop=True)
    df = df.drop_duplicates(keep="first").reset_index(drop=True)
    try:
        file = Path(f"{folder}/{stem}.parquet.gzip")
        df.to_parquet(file, compression="gzip", index=False)
    except (ArrowInvalid, ArrowTypeError):
        file.unlink(missing_ok=True)
        try:
            file = Path(f"{folder}/{stem}.fth")
            df.to_feather(file)
        except (ArrowInvalid, ArrowTypeError):
            file.unlink(missing_ok=True)
            try:
                file = Path(f"{folder}/{stem}.xlsx")
                with pd.ExcelWriter(file) as wb:
                    df.to_excel(
                        wb, sheet_name="DataBase", engine="openpyxl", index=False
                    )
            except Exception as e:
                raise ValueError(f"Could not save {stem} to {file}") from e
    return df

# %% ../nbs/updates.ipynb 9
def update_radcom(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Atualiza a tabela local retornada pela query `RADCOM`"""
    console = Console()
    with console.status(
        "[cyan]Lendo o Banco de Dados de Radcom...", spinner="earth"
    ) as status:
        try:
            df = pd.read_sql_query(SQL_RADCOM, conn)
            return _save_df(df, folder, "radcom")
        except pyodbc.OperationalError as e:
            status.console.log(
                "Não foi possível abrir uma conexão com o SQL Server. Esta conexão somente funciona da rede cabeada!"
            )
            raise ConnectionError from e

# %% ../nbs/updates.ipynb 12
def update_stel(
    conn: pyodbc.Connection,  # Objeto de conexão de banco
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Atualiza a tabela local retornada pela query `STEL`"""
    console = Console()
    with console.status(
        "[red]Lendo o Banco de Dados do STEL. Processo Lento, aguarde...",
        spinner="bouncingBall",
    ) as status:
        try:
            df = pd.read_sql_query(SQL_STEL, conn)
            return _save_df(df, folder, "stel")
        except pyodbc.OperationalError as e:
            status.console.log(
                "Não foi possível abrir uma conexão com o SQL Server. Esta conexão somente funciona da rede cabeada!"
            )
            raise ConnectionError from e

# %% ../nbs/updates.ipynb 14
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
        query = {}
        list_data = list(collection.find(query, projection=MONGO_SRD))
        mosaico_df = pd.json_normalize(list_data)
        mosaico_df = mosaico_df.drop(columns=["estacao"])
        columns = list(COLS_SRD.keys())
        mosaico_df = mosaico_df[columns]
        mosaico_df.rename(COLS_SRD, axis=1, inplace=True)
        df = clean_mosaico(mosaico_df, folder)
    return _save_df(mosaico_df, folder, "mosaico")

# %% ../nbs/updates.ipynb 17
def update_telecom(
    mongo_client: MongoClient,  # Objeto de conexão com o MongoDB
    folder: Union[str, Path],  # Pasta onde salvar os arquivos
) -> pd.DataFrame:  # DataFrame com os dados atualizados
    """Efetua a query na tabela `licenciamento` no banco mongoDB `mongo_client` e atualiza o arquivo local"""

    console = Console()
    with console.status(
        "Consolidando os dados do Licenciamento...", spinner="clock"
    ) as status:

        database = mongo_client["sms"]
        collection = database["licenciamento"]
        c = collection.find(
            MONGO_TELECOM, projection={k: 1.0 for k in COLS_TELECOM.keys()}
        )
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
        df.loc[:, ["BW(kHz)", "Classe_Emissão"]] = df.Designacao_Emissão.apply(
            parse_bw
        ).tolist()
        df.drop("Designacao_Emissão", axis=1, inplace=True)
        subset = [
            "Entidade",
            "Longitude",
            "Latitude",
            "Classe",
            "Frequência",
            "Num_Serviço",
            "BW(kHz)",
            "Classe_Emissão",
        ]
        df_sub = (
            df[~df.duplicated(subset=subset, keep="first")]
            .reset_index(drop=True)
            .copy()
        )
        df_sub = df_sub.set_index(subset).sort_index()
        df_sub["Count"] = (df.groupby(subset).count()["Número_Estação"]).tolist()
        df_sub["Count"] = df_sub["Count"].astype("string")
        df_sub.loc[df_sub.Count != "1", "Número_Estação"] = (
            df_sub.loc[df_sub.Count != "1", "Número_Estação"]
            + "+"
            + df_sub.loc[df_sub.Count != "1", "Count"]
        )
        df_sub.drop("Count", axis=1, inplace=True)
        del df
        gc.collect()
        df_sub = df_sub.reset_index()
    return _save_df(df_sub, folder, "telecom")

# %% ../nbs/updates.ipynb 19
def valida_coord(
    conn: pyodbc.Connection, row  # Objeto de conexão de banco
) -> pd.DataFrame:  # DataFrame com dados do município

    # sql_params = (row['cod_municipio'], row['latitude'], row['longitude'])
    # df = pd.read_sql(SQL_VALIDA_COORD, conn, params = sql_params)
    if row["Código_Município"].strip():

        row["Longitude"] = row["Longitude"] if row["Longitude"] else "0"
        row["Latitude"] = row["Latitude"] if row["Latitude"] else "0"

        sql = SQL_VALIDA_COORD.format(
            row["Longitude"], row["Latitude"], row["Código_Município"]
        )
        # print(sql)
        crsr = conn.cursor()
        crsr.execute(sql)
        result = crsr.fetchone()
        # print(result)
        if result == None:
            return (row["Município"], row["Longitude"], row["Latitude"], 9)
        elif result.COORD_VALIDA == 1:
            return result
        else:
            return (
                result.NO_MUNICIPIO,
                result.NU_LONGITUDE,
                result.NU_LATITUDE,
                result.COORD_VALIDA,
            )
    else:
        return (row["Município"], row["Longitude"], row["Latitude"], 9)

# %% ../nbs/updates.ipynb 20
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
    ).loc[:, TELECOM]
    radcom = update_radcom(conn, folder).loc[:, SRD]
    mosaico = update_mosaico(clientMongoDB, folder).loc[:, RADIODIFUSAO]
    telecom = update_telecom(clientMongoDB, folder)

    # Filtrando RADCOM
    radcom["Num_Serviço"] = "231"
    radcom["Status"] = "RADCOM"
    radcom["Classe_Emissão"] = pd.NA
    radcom["BW(kHz)"] = "256"
    radcom["Entidade"] = radcom.Entidade.str.rstrip().str.lstrip()
    radcom["Validade_RF"] = pd.NA
    radcom["Fonte"] = "SRD"
    # Filtrando STEL
    stel["Status"] = "L"
    stel["Entidade"] = stel.Entidade.str.rstrip().str.lstrip()
    stel["Fonte"] = "STEL"
    stel.loc[:, ["BW(kHz)", "Classe_Emissão"]] = (
        stel.Largura_Emissão.fillna("").apply(parse_bw).tolist()
    )
    stel.loc[stel.Classe_Emissão == "", "Classe_Emissão"] = pd.NA
    stel.drop("Largura_Emissão", axis=1, inplace=True)
    # Filtrando MOSAICO
    mosaico["Fonte"] = "MOS"
    mosaico.loc[:, ["BW(kHz)", "Classe_Emissão"]] = (
        mosaico.Num_Serviço.map(BW_MAP).apply(parse_bw).tolist()
    )
    mosaico.loc[mosaico.Classe_Emissão == "", "Classe_Emissão"] = pd.NA

    # Filtrando LICENCIAMENTO
    telecom["Fonte"] = "LIC"

    rd = (
        # pd.concat([mosaico, radcom, stel])
        pd.concat([mosaico, radcom, stel, telecom])
        .sort_values(["Frequência", "Latitude", "Longitude"])
        .reset_index(drop=True)
    )
    rd = rd.drop_duplicates(keep="first").reset_index(drop=True)

    # Verificando conteúdo do CSV Final
    # filepath = Path(f"\\\\servrepds\\dw$\\Input\\sentinela\\update_base.csv")
    # rd.to_csv(filepath)

    # Validando Coordenadas
    rd["coord_valida"] = None
    rd[["Município", "Longitude", "Latitude", "coord_valida"]] = rd.apply(
        lambda row: pd.Series(list(valida_coord(conn, row))), axis=1
    )
    rd = rd.drop(rd[rd.coord_valida == 9].index)

    return _save_df(rd, folder, "base")
