import os
import warnings
import typer
from pymongo import MongoClient
from fastcore.xtras import Path
from extracao.updates import connect_db
from extracao.main import get_db

warnings.filterwarnings("ignore")

def run_request(folder:str=os.environ['FOLDER'], update:bool=False)->None:
    """Executa a consolidação dos arquivos das diversas bases de dados
    Opcionalmente faz a atualização de todos caso update=True"""
    folder = Path(folder)
    assert folder.is_dir(), f"A pasta {folder} não é válida!"
    conn, mongo_client = None, None
    if update:
        conn = connect_db()
        mongo_client = MongoClient(os.environ['MONGO_URI'])
    get_db(folder, conn, mongo_client)
        
    

if __name__ == '__main__':
    conn = connect_db()
    uri = os.environ['MONGO_URI']
    mongo_client = MongoClient(uri)
    mongo_client.server_info()
    typer.run(run_request)
