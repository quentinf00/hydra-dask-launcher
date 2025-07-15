# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import logging
from pathlib import Path
from typing import Any, Optional, Sequence
from dask.distributed import Client, LocalCluster
from joblib import Parallel, delayed
from hydra.plugins.launcher import Launcher
from hydra.core.hydra_config import HydraConfig
from hydra.core.singleton import Singleton
from hydra.types import HydraContext, TaskFunction
from omegaconf import DictConfig
from omegaconf import DictConfig, open_dict
from hydra.core.utils import (
    JobReturn,
    configure_log,
    filter_overrides,
    run_job,
    setup_globals,
)
from hydra.utils import instantiate

log = logging.getLogger(__name__)


def execute_job(
    idx: int,
    overrides: Sequence[str],
    hydra_context: HydraContext,
    config: DictConfig,
    task_function: TaskFunction,
    singleton_state: dict[Any, Any],
) -> JobReturn:
    """Calls `run_job` in parallel"""
    setup_globals()
    Singleton.set_state(singleton_state)

    sweep_config = hydra_context.config_loader.load_sweep_config(
        config, list(overrides)
    )
    with open_dict(sweep_config):
        sweep_config.hydra.job.id = f"{sweep_config.hydra.job.name}_{idx}"
        sweep_config.hydra.job.num = idx
    HydraConfig.instance().set_config(sweep_config)

    ret = run_job(
        hydra_context=hydra_context,
        config=sweep_config,
        task_function=task_function,
        job_dir_key="hydra.sweep.dir",
        job_subdir_key="hydra.sweep.subdir",
    )

    return ret


class DaskLauncher(Launcher):
    def __init__(self, **kwargs: Any) -> None:
        """Dask Launcher"""
        self.config: Optional[DictConfig] = None
        self.task_function: Optional[TaskFunction] = None
        self.hydra_context: Optional[HydraContext] = None
        self.cluster = None
        self.client = None
        self.parallel_config = None

        self.dask = kwargs

    def setup(
        self,
        *,
        hydra_context: HydraContext,
        task_function: TaskFunction,
        config: DictConfig,
    ) -> None:
        self.config = config
        self.task_function = task_function
        self.hydra_context = hydra_context
        
        self.job = self.config.hydra.launcher

    def launch(
        self, job_overrides: Sequence[Sequence[str]], initial_job_idx: int
    ) -> Sequence[JobReturn]:
        setup_globals()

        configure_log(self.config.hydra.hydra_logging, self.config.hydra.verbose)
        sweep_dir = Path(str(self.config.hydra.sweep.dir))
        sweep_dir.mkdir(parents=True, exist_ok=True)

        log.info(f"Launching jobs, sweep output dir : {sweep_dir}")
        for idx, overrides in enumerate(job_overrides):
            log.info("\t#{} : {}".format(idx, " ".join(filter_overrides(overrides))))

        singleton_state = Singleton.get_state()

        if self.cluster == "local":
            log.info("Using default local Dask cluster.")
            self.cluster = LocalCluster()
        else:
            log.info("Instantiating Dask cluster.")
            self.cluster = instantiate(self.job.cluster)
        log.debug(f"Cluster: {self.cluster}")

        if self.job.scale_kwargs:
            self.cluster.scale(**self.job.scale_kwargs)
        elif self.job.adapt_kwargs:
            self.cluster.adapt(**self.job.adapt_kwargs)

        if self.cluster is None:
            log.info(
                "No Dask cluster provided, external cluster should be configured in client."
            )
            self.client = instantiate(self.job.client)
        else:
            self.client = instantiate(self.job.client, self.cluster)
        log.info(f"Using client : {self.client}")
        log.info(f"Dashboard at : {self.client.dashboard_link}")
        with instantiate(self.job.parallel_config):
            runs = Parallel()(
                delayed(execute_job)(
                    initial_job_idx + idx,
                    overrides,
                    self.hydra_context,
                    self.config,
                    self.task_function,
                    singleton_state,
                )
                for idx, overrides in enumerate(job_overrides)
            )

        assert isinstance(runs, list)
        for run in runs:
            assert isinstance(run, JobReturn)
        return runs
