# AUTOGENERATED! DO NOT EDIT! File to edit: ..\nbs\redemet.ipynb.

# %% auto 0
__all__ = ['URL', 'get_redemet']

# %% ..\nbs\redemet.ipynb 2
import os
import json
from datetime import datetime
from urllib.request import urlopen
import pandas as pd
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# %% ..\nbs\redemet.ipynb 5
URL = "https://api-redemet.decea.mil.br/produtos/radar/maxcappi?api_key={}&{}"


# %% ..\nbs\redemet.ipynb 6
def get_redemet() -> (
    pd.DataFrame
):  # DataFrame com frequências, coordenadas e descrição das estações VOR
    # sourcery skip: use-fstring-for-concatenation
    """Faz a requisição get à API do REDEMET usanda a chave `apikey`, processa o json e o retorna como Dataframe"""
    load_dotenv()
    date = datetime.now().strftime("%Y%m%d")
    link = URL.format(os.environ["RMETKEY"], date)
    response = urlopen(link)
    if (
        response.status != 200
        or "application/json" not in response.headers["content-type"]
    ):
        raise ValueError(
            f"Resposta a requisição não foi bem sucedida: {response.status=}"
        )
    data_json = json.loads(response.read())
    df = pd.json_normalize(
        data_json["data"]["radar"][0],
    )
    df["Frequency"] = "2800"
    df["Description"] = "[RMET] " + df.nome.astype("string")
    df = df[["Frequency", "lat_center", "lon_center", "Description"]].astype(
        "string", copy=False
    )
    return df.rename(columns={"lat_center": "Latitude", "lon_center": "Longitude"})
