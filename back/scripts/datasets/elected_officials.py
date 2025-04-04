import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from back.scripts.loaders.base_loader import BaseLoader
from back.scripts.utils.config import get_project_base_path
from back.scripts.utils.datagouv_api import DataGouvAPI
from back.scripts.utils.decorators import tracker

LOGGER = logging.getLogger(__name__)

RENAME_COMMON_COLUMNS = {
    "Nom de l'élu": "nom",
    "Prénom de l'élu": "prenom",
    "Code sexe": "sexe",
    "Date de naissance": "date_naissance",
    "Code de la catégorie socio-professionnelle": "code_socio_pro",
    "Libellé de la catégorie socio-professionnelle": "lib_socio_pro",
    "Date de début du mandat": "date_debut_mandat",
    "Date de début de la fonction": "date_debut_fonction",
    "Code du département": "code_dept",
    "Code de la commune": "code_commune",
    "Code du canton": "code_canton",
    "Libellé du canton": "lib_canton",
    "Code de la région": "code_region",
    "Libellé de la région": "lib_region",
    "Code de la section départementale": "code_section_dept",
    "Libellé de la section départementale": "lib_section_dept",
    "Code de la circonscription législative": "code_circo",
    "Libellé de la circonscription législative": "lib_circo",
    "Code de la collectivité à statut particulier": "code_collectivite",
    "Libellé de la collectivité à statut particulier": "lib_collectivite",
    "Libellé de la fonction": "lib_fonction",
    "N° SIREN": "siren_epci",
    "Libellé de l'EPCI": "lib_epci",
    "Code de la commune de rattachement": "code_commune",
    "Code de la circonscription métropolitaine": "code_circo_metropolitaine",
    "Code de la section - collectivité à statut particulier": "code_section_collectivite",
    "Code de la circonscription consulaire": "code_circo_consulaire",
    "Code de la circonscription AFE": "code_circo_afe",
    "Code de la circ. AFE": "code_circo_afe",
}


class ElectedOfficialsWorkflow:
    DATASET_ID = "5c34c4d1634f4173183a64f1"

    @classmethod
    def get_config_key(cls) -> str:
        return "elected_officials"

    @classmethod
    def get_output_path(cls, main_config: dict) -> Path:
        return (
            get_project_base_path()
            / main_config[cls.get_config_key()]["data_folder"]
            / "elected_officials.parquet"
        )

    def __init__(self, main_config: dict):
        self._config = main_config[self.get_config_key()]
        self.data_folder = Path(self._config["data_folder"])
        self.data_folder.mkdir(exist_ok=True, parents=True)
        self.output_filename = self.get_output_path(main_config)

    @tracker(ulogger=LOGGER, log_start=True)
    def run(self) -> None:
        if self.output_filename.exists():
            return
        self._fetch_raw_datasets()
        self._combine_datasets()
        self.elected_officials.to_parquet(self.output_filename)

    def _fetch_raw_datasets(self):
        """
        Fetch all resources from the target dataset.
        Each resource consist in the data for a different elected position (mayor, senator, etc.).
        """
        resources = DataGouvAPI.dataset_resources(self.DATASET_ID, savedir=self.data_folder)
        self.raw_datasets = {}
        for _, resource in tqdm(resources.iterrows()):
            filename = self.data_folder / f"{resource['resource_id']}.parquet"
            if filename.exists():
                continue
            self.raw_datasets[resource["resource_description"]] = BaseLoader.loader_factory(
                resource["resource_url"]
            ).load()

    def _combine_datasets(self):
        combined = []
        for mandat, df in self.raw_datasets.items():
            present_columns = {
                k: v for k, v in RENAME_COMMON_COLUMNS.items() if k in df.columns
            }
            combined.append(
                df[present_columns.keys()].rename(columns=present_columns).assign(mandat=mandat)
            )

        self.elected_officials = (
            pd.concat(combined, ignore_index=True)
            .assign(
                date_naissance=lambda df: pd.to_datetime(
                    df["date_naissance"], dayfirst=True, errors="coerce"
                ),
                date_debut_mandat=lambda df: pd.to_datetime(
                    df["date_debut_mandat"], dayfirst=True, errors="coerce"
                ),
                code_socio_pro=lambda df: df["code_socio_pro"].astype("Int16"),
            )
            .astype(
                {
                    "code_dept": str,
                    "code_commune": str,
                    "code_canton": str,
                    "code_collectivite": str,
                }
            )
        )
