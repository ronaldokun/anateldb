# AUTOGENERATED! DO NOT EDIT! File to edit: ..\nbs\reading.ipynb.

# %% auto 0
__all__ = ['read_mosaico', 'read_telecom', 'read_radcom', 'read_stel', 'read_icao', 'read_aisw', 'read_aisg', 'read_redemet',
           'read_aero', 'read_base']

# %% ..\nbs\reading.ipynb 2
import os
from typing import Union
from pathlib import Path

import pandas as pd
from pyarrow import ArrowInvalid
import pyodbc
from pymongo import MongoClient
from dotenv import load_dotenv

from extracao.updates import (
    update_mosaico,
    update_stel,
    update_radcom,
    update_base,
    update_telecom,
)

from .icao import get_icao
from .aisgeo import get_aisg
from .aisweb import get_aisw
from .redemet import get_redemet
from .format import merge_close_rows

load_dotenv()

# %% ..\nbs\reading.ipynb 3
def _read_df(folder: Union[str, Path], stem: str) -> pd.DataFrame:
    """Lê o dataframe formado por folder / stem.[parquet.gzip | fth | xslx]"""
    file = Path(f"{folder}/{stem}.parquet.gzip")
    try:
        df = pd.read_parquet(file)
    except (ArrowInvalid, FileNotFoundError) as e:        
        raise e(f"Error when reading {file}")
    return df

# %% ..\nbs\reading.ipynb 5
def read_mosaico(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    conn: MongoClient = None,  # Objeto de Conexão com o banco MongoDB, atualiza os dados caso válido
) -> pd.DataFrame:  # Dataframe com os dados do mosaico
    """Lê o banco de dados salvo localmente do MOSAICO e opcionalmente o atualiza."""
    return update_mosaico(conn, folder) if conn else _read_df(folder, "mosaico")

# %% ..\nbs\reading.ipynb 10
def read_telecom(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    conn: MongoClient = None,  # Objeto de Conexão com o banco MongoDB, atualiza os dados caso válido
) -> pd.DataFrame:  # Dataframe com os dados do mosaico
    """Lê o banco de dados salvo localmente do LICENCIAMENTO e opcionalmente o atualiza."""
    return update_telecom(conn, folder) if conn else _read_df(folder, "telecom")

# %% ..\nbs\reading.ipynb 13
def read_radcom(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    conn: pyodbc.Connection = None,  # Objeto de conexão de banco, atualiza os dados caso válido
) -> pd.DataFrame:  # Dataframe com os dados de RADCOM
    """Lê o banco de dados salvo localmente de RADCOM. Opcionalmente o atualiza pelo Banco de Dados ANATELBDRO05 caso `update = True` ou não exista o arquivo local"""
    return update_radcom(conn, folder) if conn else _read_df(folder, "radcom")

# %% ..\nbs\reading.ipynb 16
def read_stel(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    conn: pyodbc.Connection = None,  # Objeto de conexão de banco. Atualiza os dados caso válido
) -> pd.DataFrame:  # Dataframe com os dados do STEL
    """Lê o banco de dados salvo localmente do STEL.
     Opcionalmente o atualiza pelo Banco de Dados ANATELBDRO05
    caso `update = True` ou não exista o arquivo local"""
    return update_stel(conn, folder) if conn else _read_df(folder, "stel")

# %% ..\nbs\reading.ipynb 19
def read_icao(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    update: bool = False,  # Atualiza os dados caso `True`
) -> pd.DataFrame:  # Dataframe com os dados do ICAO
    """Lê a base de dados do Frequency Finder e Canalização VOR/ILS/DME"""
    return get_icao if update else _read_df(folder, "icao")

# %% ..\nbs\reading.ipynb 20
def read_aisw(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    update: bool = False,  # Atualiza os dados caso `True`
) -> pd.DataFrame:  # Dataframe com os dados do AISWEB
    """Fontes da informação: AISWEB, REDEMET, Ofício nº 2/SSARP/14410 e Canalização VOR/ILS/DME."""
    return get_aisw() if update else _read_df(folder, "aisw")

# %% ..\nbs\reading.ipynb 21
def read_aisg(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    update: bool = False,  # Atualiza os dados caso `True`
) -> pd.DataFrame:  # Dataframe com os dados do GEOAISWEB
    """Fontes da informação: GEOAISWEB, REDEMET, Ofício nº 2/SSARP/14410 e Canalização VOR/ILS/DME."""
    return get_aisg() if update else _read_df(folder, "aisg")

# %% ..\nbs\reading.ipynb 22
def read_redemet(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    update: bool = False,  # Atualiza os dados caso `True`
) -> pd.DataFrame:  # Dataframe com os dados do AISWEB
    """Fontes da informação: AISWEB, REDEMET, Ofício nº 2/SSARP/14410 e Canalização VOR/ILS/DME."""
    return get_redemet() if update else _read_df(folder, "redemet")

# %% ..\nbs\reading.ipynb 23
def read_aero(
    folder: Union[str, Path],  # Pasta onde ler/salvar os dados
    update: bool = False,  # Atualiza os dados caso `True`
) -> pd.DataFrame:  # Dataframe com os dados mesclados das 3 bases da Aeronáutica anteriores
    """Lê os arquivos de dados da aeronáutica e retorna os registros comuns e únicos"""
    if not update:
        return _read_df(folder, "aero")
    icao = get_icao()
    aisw = get_aisw()
    aisg = get_aisg()
    redemet = get_redemet()
    radares = pd.read_excel(os.environ['PATH_RADAR'])
    for df in [aisw, aisg, redemet, radares]:
        icao = merge_close_rows(icao, df)
    return icao

# %% ..\nbs\reading.ipynb 26
def read_base(
    folder: Union[str, Path],
    conn: pyodbc.Connection = None,  # Objeto de conexão do banco SQL Server
    clientMongoDB: MongoClient = None,  # Objeto de conexão do banco MongoDB
) -> pd.DataFrame:
    """Lê a base de dados e opcionalmente a atualiza antes da leitura casos as conexões de banco sejam válidas"""
    return (
        update_base(conn, clientMongoDB, folder)
        if all([conn, clientMongoDB])
        else _read_df(folder, "base")
    )
