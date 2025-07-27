import click
from typing import Any
from pathlib import Path
from datetime import datetime as dt

from src.pipelines import (
    collect_notion_data,
    etl_pipeline,
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
    "--run-collect-notion-data-pipeline",
    is_flag=True,
    default=False,
    help="Whether to run the collect_notion_data pipeline"
)
@click.option(
    "--run-etl-pipeline",
    is_flag=True,
    default=False,
    help="Whether to run the etl pipeline"
)
@click.option(
    "--run-feature-pipeline",
    is_flag=True,
    default=False,
    help="Whether to run the feature pipeline"
)
def main(
    no_cache: bool = False,
    run_collect_notion_data_pipeline: bool = False,
    run_etl_pipeline: bool = False,
    run_feature_pipeline: bool = False
) -> None:
    assert(
        run_collect_notion_data_pipeline
        or run_etl_pipeline
        or run_feature_pipeline
    ), "Please specify an action to run."
    
    pipeline_args: dict[str, Any] = {
        "enable_cache": not no_cache
    }
    root_dir = Path(__file__).resolve().parent.parent
    # print(Path(__file__).resolve())
    if run_collect_notion_data_pipeline:
        pipeline_args["config_path"] = root_dir / "configs" / "collect_notion_data.yaml"
        assert pipeline_args["config_path"].exists(), (
            f"Config file not found: {pipeline_args['config_path']}"
        )
        pipeline_args["run_name"] = (
            f"collect_notion_data_run{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        )
        collect_notion_data.collect_notion_data.with_options(**pipeline_args)()

    if run_etl_pipeline:
        pipeline_args["config_path"] = root_dir / "configs" / "etl_pipeline.yaml"
        assert pipeline_args["config_path"].exists(), (
            f"Config file not found: {pipeline_args['config_path']}"
        )
        pipeline_args["run_name"] = (
            f"feature_pipeline_run{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        )
        etl_pipeline.etl.with_options(**pipeline_args)()

    if run_feature_pipeline:
        pipeline_args["config_path"] = root_dir / "configs" / "feature_pipeline.yaml"
        assert pipeline_args["config_path"].exists(), (
            f"Config file not found: {pipeline_args['config_path']}"
        )
        pipeline_args["run_name"] = (
            f"feature_pipeline_run{dt.now().strftime('%Y_%m_%d_%H_%M_%S')}"
        )
        feature_pipeline.feature_pipeline.with_options(**pipeline_args)()

if __name__ == "__main__":
    main()