import json
import logging
from itertools import chain
from pathlib import Path

import pandas as pd

from back.scripts.loaders.base_loader import retry_session
from back.scripts.loaders.utils import LOADER_CLASSES

LOGGER = logging.getLogger(__name__)


class DataGouvAPI:
    def __init__(self):
        raise Exception("Utility class.")

    @staticmethod
    def get_stable_file_url(file_id: str) -> str:
        return f"https://www.data.gouv.fr/fr/datasets/r/{file_id}"

    @classmethod
    def dataset_resources(cls, dataset_id: str, savedir: Path | None = None) -> pd.DataFrame:
        """
        Fetch information about all resources of a given dataset.
        """
        savedir = Path(savedir or ".")
        savedir.mkdir(exist_ok=True, parents=True)
        save_filename = savedir / f"dataset_{dataset_id}.parquet"
        if savedir and save_filename.exists():
            return pd.read_parquet(save_filename)

        url = f"https://www.data.gouv.fr/api/1/datasets/{dataset_id}/"
        datasets = []
        while url:
            metadata, url = cls._next_page(url)
            datasets.append(
                [
                    {
                        "dataset_id": metadata["id"],
                        "title": metadata["title"],
                        "description": metadata["description"],
                        "frequency": metadata["frequency"],
                    }
                    | cls._resource_infos(resource)
                    | cls._organisation_infos(metadata["organization"])
                    for resource in metadata["resources"]
                ]
            )
        datasets = pd.DataFrame(
            list(chain.from_iterable(datasets)),
            columns=[
                "dataset_id",
                "title",
                "description",
                "frequency",
                "created_at",
                "resource_id",
                "resource_url",
                "format",
                "resource_description",
                "organization_id",
                "organization",
            ],
        )
        if savedir:
            datasets.to_parquet(save_filename)
        return datasets

    @classmethod
    def organisation_datasets(
        cls, organization_id: str, savedir: Path | None = None
    ) -> pd.DataFrame:
        """
        Fetch information about all datasets and resources of a given organization.
        """
        savedir = Path(savedir or ".")
        savedir.mkdir(exist_ok=True, parents=True)
        organisation_datasets_filename = savedir / f"orga_{organization_id}.parquet"
        if savedir and organisation_datasets_filename.exists():
            return pd.read_parquet(organisation_datasets_filename)

        url = "https://www.data.gouv.fr/api/1/datasets/"
        params = {"organization": organization_id}
        datasets = []
        output_columns = [
            "organization_id",
            "organization",
            "title",
            "description",
            "dataset_id",
            "frequency",
            "format",
            "url",
            "created_at",
            "resource_description",
            "deleted_dataset",
            "resource_id",
            "resource_url",
        ]
        try:
            while url:
                orga_datasets, url = cls._next_page(url, params)
                datasets.append(
                    [
                        {
                            "organization_id": metadata["organization"]["id"],
                            "organization": metadata["organization"]["name"],
                            "title": metadata["title"],
                            "description": metadata["description"],
                            "dataset_id": metadata["id"],
                            "frequency": metadata["frequency"],
                            "created_at": resource["created_at"],
                        }
                        | cls._resource_infos(resource)
                        for metadata in orga_datasets
                        for resource in metadata["resources"]
                    ]
                )
        except Exception:
            LOGGER.error("Error while downloading file from %s", url)
            return pd.DataFrame(columns=output_columns)

        datasets = pd.DataFrame(list(chain.from_iterable(datasets)), columns=output_columns)
        if savedir:
            datasets.to_parquet(organisation_datasets_filename)
        return datasets

    @staticmethod
    def _resource_infos(resource: dict) -> dict:
        return {
            "resource_id": resource["id"],
            "resource_url": resource["url"],
            "format": resource["format"],
            "created_at": resource["created_at"],
            "resource_description": resource["description"],
        }

    @staticmethod
    def _organisation_infos(organization: dict) -> dict:
        return {"organization_id": organization["id"], "organization": organization["name"]}

    @staticmethod
    def _next_page(url: str, params: dict | None = None) -> tuple[dict, str]:
        """
        Fetch the content of a given page and eventually the link to the next page.
        """
        session = retry_session(retries=5)
        response = session.get(url, params=params)
        try:
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Error while downloading file from {url} : {e}")
            return {}, ""
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            logging.error(f"Error while decoding json from {url} : {e}")
            return {}, ""
        return data.get("data", data), data.get("next_page")


def select_implemented_formats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Select datasets for which we implemented a reader for their formats.
    Log formats to be added.
    """
    valid_formats = df["format"].isin(LOADER_CLASSES.keys())
    incorrects = df.loc[~valid_formats, "format"].dropna().value_counts().to_dict()
    LOGGER.info("Non implemented file formats: %s", incorrects)
    return df[valid_formats]
