from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from dask.distributed import Client

from hydra.core.config_store import ConfigStore


@dataclass
class DaskLauncherConf:
    """Dask launcher configuration."""

    _target_: str = "hydra_plugins.hydra_dask_launcher.launcher.DaskLauncher"
    verbose: int = 0
    cluster: Optional[Any] = None
    scale_kwargs: Optional[Dict[str, Any]] = None
    client: Optional[Dict[str, Any]] = None
    adapt_kwargs: Optional[Dict[str, Any]] = None
    parallel_config: Optional[Dict[str, Any]] = None
    _recursive_: bool = False


def setup_config() -> None:
    """Set up the configuration store for the Joblib launcher."""
    cs = ConfigStore.instance()
    parallel_config = {
        "_target_": "joblib.parallel_config",
        "backend": "dask",
        "verbose": 0,
    }
    cluster = {
        "_target_": "dask.distributed.LocalCluster",
    }
    client = {
        "_target_": "dask.distributed.Client",
    }
    cs.store(
        group="hydra/launcher",
        package="hydra.launcher",
        name="dask",
        node=DaskLauncherConf(cluster=cluster, parallel_config=parallel_config, client=client),
        provider="dask_launcher",
    )
