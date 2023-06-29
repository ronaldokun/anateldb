import os
import shutil
import warnings
from datetime import datetime
import typer
from pymongo import MongoClient
from fastcore.xtras import Path
from extracao.updates import connect_db
from extracao.main import get_db

warnings.filterwarnings("ignore")


def run_request(folder: str = os.environ["FOLDER"], update: bool = False) -> None:
    """Executa a consolidação dos arquivos das diversas bases de dados
    Opcionalmente faz a atualização de todos caso update=True"""
    start = datetime.now()
    folder = Path(folder)
    assert folder.is_dir(), f"A pasta {folder} não é válida!"
    conn, mongo_client = None, None
    if update:
        conn = connect_db()
        mongo_client = MongoClient(os.environ["MONGO_URI"])
    get_db(folder, conn, mongo_client)
    source = Path(os.environ["FOLDER"])
    dest = str(Path(os.environ["DESTINATION"]))
    outputs = ("AnatelDB.parquet.gzip", "VersionFile.json")
    for out in outputs:
        shutil.copy(f"{source / out}", dest)
    print(f"Tempo total decorrido: {datetime.now() - start}")


if __name__ == "__main__":
    typer.run(run_request)
