import logging
import time

log = logging.getLogger(__name__)

def add(a, b):
    """Add two numbers."""
    log.info(f"Adding {a} and {b}")
    time.sleep(3)  # Simulate a delay
    return a + b


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(level)s- %(name)s - %(levelname)s - %(message)s")
    import hydra
    from hydra.core.config_store import ConfigStore
    
    cs = ConfigStore.instance()
    cs.store(name="add", node={ "_target_": "test_dask_launcher.add", "a": 1, "b": 2})

    cs.store(name="local_default", node={ "cluster": "local"}, package="hydra/launcher")
    cs.store(name="local_cluster", node=dict(_target_='dask.distributed.LocalCluster', n_workers=2, threads_per_worker=2, memory_limit="2GiB"), group="dask", package="hydra.launcher.cluster")
    
    hydra.main(version_base="1.3", config_name="add")(hydra.utils.instantiate)()