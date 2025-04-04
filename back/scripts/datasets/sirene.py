import logging
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import polars as pl
from polars import col

from back.scripts.utils.config import get_project_base_path
from back.scripts.utils.decorators import tracker

LOGGER = logging.getLogger(__name__)

# Source : http://freturb.laet.science/tables/Sirextra.htm
EFFECTIF_CODE_TO_EMPLOYEES = {
    "00": 0,
    "01": 1,
    "02": 3,
    "03": 6,
    "11": 10,
    "12": 20,
    "21": 50,
    "22": 100,
    "31": 200,
    "41": 500,
    "42": 1000,
    "51": 2000,
    "52": 5000,
}


class SireneWorkflow:
    """
    https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
    """

    @classmethod
    def get_config_key(cls) -> str:
        return "sirene"

    @classmethod
    def get_output_path(cls, main_config: dict) -> Path:
        return (
            get_project_base_path()
            / main_config[cls.get_config_key()]["data_folder"]
            / "sirene.parquet"
        )

    def __init__(self, main_config: dict):
        self._config = main_config[self.get_config_key()]
        self.data_folder = Path(self._config["data_folder"])
        self.data_folder.mkdir(exist_ok=True, parents=True)

        self.input_filename = self.data_folder / "sirene.zip"
        self.output_filename = self.get_output_path(main_config)

    @tracker(ulogger=LOGGER, log_start=True)
    def run(self) -> None:
        if self.output_filename.exists():
            return
        self._fetch_zip()
        self._format_to_parquet()

    def _fetch_zip(self):
        if self.input_filename.exists():
            return
        urllib.request.urlretrieve(self._config["url"], self.input_filename)

    def _format_to_parquet(self):
        if self.output_filename.exists():
            return

        with tempfile.TemporaryDirectory() as tmpdirname:
            with zipfile.ZipFile(self.input_filename) as zip_ref:
                zip_ref.extractall(tmpdirname)
                csv_fn = Path(tmpdirname) / "StockUniteLegale_utf8.csv"
                pl.scan_csv(
                    csv_fn, schema_overrides={"trancheEffectifsUniteLegale": pl.String}
                ).select(
                    col("siren").cast(pl.String).str.zfill(9),
                    (col("etatAdministratifUniteLegale") == "A").alias("is_active"),
                    pl.coalesce(
                        col("nomUsageUniteLegale"),
                        col("denominationUniteLegale"),
                        col("nomUniteLegale"),
                    ).alias("raison_sociale"),
                    col("prenomUsuelUniteLegale").alias("raison_sociale_prenom"),
                    col("activitePrincipaleUniteLegale")
                    .str.replace_all(".", "", literal=True)
                    .alias("naf8"),
                    col("categorieJuridiqueUniteLegale").alias("code_ju"),
                    col("trancheEffectifsUniteLegale")
                    .replace_strict(EFFECTIF_CODE_TO_EMPLOYEES, default=None)
                    .cast(pl.Int32)
                    .alias("tranche_effectif"),
                ).collect().write_parquet(self.output_filename)
