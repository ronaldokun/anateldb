import sys
from pathlib import Path

sys.path.insert(0, str(Path().cwd()))


import os
from fastcore.xtras import Path
from time import perf_counter
import pandas as pd
from pymongo import MongoClient
from dotenv import find_dotenv, load_dotenv
from ydata_profiling import ProfileReport

start = perf_counter()

load_dotenv(find_dotenv())
uri = os.environ["MONGO_URI"]
mongo_client = MongoClient(uri)
mongo_client.server_info()

database = mongo_client["sms"]

# for c in database.list_collection_names():
#     pprint(c)
#     pprint(database[c].find_one())
#     pprint(20*'=')

MONGO_SMP = {
    "$and": [
        # {"DataExclusao": None},
        {"DataValidade": {"$nin": ["", None]}},
        {"Status.state": "LIC-LIC-01"},
        {"NumServico": "010"},
        {"FreqInicialMHz": {"$nin": [None, "", 0]}},
        {"FreqCentralMHz": {"$nin": [None, "", 0]}},
        {"FreqFinalMHz": {"$nin": [None, "", 0]}},
        # {"CodMunicipio": {"$nin": [None, ""]}}
        # {"Latitude": {"$type": 1.0}},
        # {"Longitude": {"$type": 1.0}}
    ]
}

COLS_SMP = {
    "NumAto": "Num_Ato",
    "NumFistel": "Fistel",
    "NomeEntidade": "Entidade",
    "SiglaUf": "UF",
    "NumEstacao": "Número_Estação",
    "NomeMunicipio": "Município",
    "CodMunicipio": "Código_Município",
    "DataValidade": "Validade_RF",
    "FreqInicialMHz": "Frequência_Inicial",
    "FreqCentralMHz": "Frequência_Central",
    "FreqFinalMHz": "Frequência_Final",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    "DesignacaoEmissao": "Designacao_Emissão",
    "PotenciaTransmissorWatts": "Potência(W)",
    "CodTipoAntena": "Cod_TipoAntena",
    "Polarizacao": "Polarização",
    "RaioAntena": "Raio_Antena",
    "GanhoAntena": "Ganho_Antena",
    "FrenteCostaAntena": "FC_Antena",
    "AnguloMeiaPotenciaAntena": "Ang_MP_Antena",
    "AnguloElevacao": "Ângulo_Elevação",
    "Azimute": "Azimute",
    "AlturaAntena": "Altura_Antena",
    "PerdasAcessorias": "Perdas_Acessorias",
}

DTYPE_SMP = {
    "NumAto": "category",
    "NumFistel": "category",
    "NomeEntidade": "category",
    "SiglaUf": "category",
    "NumEstacao": "string",
    "NomeMunicipio": "category",
    "CodMunicipio": "category",
    "DataValidade": "category",
    "FreqInicialMHz": "category",
    "FreqCentralMHz": "category",
    "FreqFinalMHz": "category",
    "Latitude": "float",
    "Longitude": "float",
    "DesignacaoEmissao": "category",
    "PotenciaTransmissorWatts": "float",
    "CodTipoAntena": "category",
    "Polarizacao": "category",
    "RaioAntena": "float",
    "GanhoAntena": "float",
    "FrenteCostaAntena": "float",
    "AnguloMeiaPotenciaAntena": "float",
    "AnguloElevacao": "float",
    "Azimute": "float",
    "AlturaAntena": "float",
    "PerdasAcessorias": "float",
}

collection = database["licenciamento"]

query = collection.find(MONGO_SMP, projection={k: 1.0 for k in COLS_SMP}, limit=0)

df = pd.DataFrame(list(query))  # , columns=COLS_SMP.keys())
df.drop(columns=["_id"], inplace=True)

for k, v in DTYPE_SMP.items():
    if "float" in v:
        df[k] = pd.to_numeric(df[k], errors="coerce")
    try:
        df[k] = df[k].astype(v)
    except Exception as e:
        print(e)
        print(k)


df.astype("string").to_parquet(
    "dados/smp_formated.parquet.gzip",
    compression="gzip",
    index=False,
)

profile = ProfileReport(df, minimal=True, title="Entidades SMP")

profile.to_file("dados/relatorio_smp.html")

print(f"Total time (asynchronous): {perf_counter() - start}")
