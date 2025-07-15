# hydra-dask-launcher

A Hydra plugin for launching jobs on Dask clusters. This plugin allows you to scale your Hydra-powered experiments or workflows using Dask's distributed computing capabilities.

## Installation

```bash
conda install quentinf00::hydra-dask-launcher
```

## Usage

Add the plugin to your Hydra configuration:

`config/launcher/local_dask`
```yaml
# @package hydra.launcher
_target_: hydra_plugins.hydra_dask_launcher.launcher.DaskLauncher
verbose: 0
cluster:
  _target_: dask.distributed.LocalCluster
  n_workers: 2
  threads_per_worker: 2
  memory_limit: 2GiB
scale_jobs: null
client:
  _target_: dask.distributed.Client
adapt_kwargs: null
parallel_config:
  _target_: joblib.parallel_config
  backend: dask
  verbose: 0
_recursive_: false

```

### Example: Launching with Dask

Suppose you have a script `my_app.py`:

```python
import hydra

@hydra.main(config_path="config.yaml")
def my_app(cfg):
        print(f"Running with param={cfg.param}")

if __name__ == "__main__":
        my_app()
```

You can launch multiple jobs in parallel using Hydra's multirun:

```bash
python my_app.py -m +launcher=local_dask myparam=1,2,3
```

With the Dask launcher configured, each job will be submitted to the Dask cluster.


## License

MIT License