import click
from typing import Any
from pathlib import Path
from datetime import datetime as dt

from src.pipelines import (
    feature_pipeline
)

@click.command()
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Disable caching for the pipeline run"
)
@click.option(
    "--run-feature-pipeline",
    is_flag=True,
    default=False,
    help="Whether to run the feature pipeline"
)
def main(
    no_cache: bool = False,
    run_feature_pipeline: bool = False
) -> None:
    assert(run_feature_pipeline
           ), "Please specify an action to run."
    
    pipeline_args: dict[str, Any] = {
        "enable_cache": not no_cache
    }
    root_dir = Path(__file__).resolve().parent.parent
    print(Path(__file__).resolve)

    if run_feature_pipeline:
        run_args = {}
        pipeline_args["config_path"] = root_dir / "configs" / "feature_pipeline.yaml"
        assert pipeline_args["config_path"].exists(), (
            f"Config file not found: {pipeline_args['config_path']}"
        )
        pipeline_args["run_name"] = (
            f"feature_pipeline_run{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        )
        feature_pipeline.feature_pipeline.with_options(**pipeline_args)(**run_args)

if __name__ == "__main__":
    main()