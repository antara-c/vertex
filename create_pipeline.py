import kfp
from google.cloud import aiplatform
from google_cloud_pipeline_components import aiplatform as gcc_aip

project_id = "vi-teting-project"
pipeline_root_path = "gs://ravi-test-003/passenger.csv"

# Define the workflow of the pipeline.
@kfp.dsl.pipeline(
    name="antara-training",
    pipeline_root=pipeline_root_path)
def pipeline(project_id: str):
    # The first step of your workflow is a dataset generator.
    # This step takes a Google Cloud pipeline component, providing the necessary
    # input arguments, and uses the Python variable `ds_op` to define its
    # output. Note that here the `ds_op` only stores the definition of the
    # output but not the actual returned object from the execution. The value
    # of the object is not accessible at the dsl.pipeline level, and can only be
    # retrieved by providing it as the input to a downstream component.
    ds_op = gcc_aip.ImageDatasetCreateOp(
        project=project_id,
        display_name="passenger",
        gcs_source="gs://ravi-test-003/passenger.csv",
        import_schema_uri=aiplatform.schema.dataset.ioformat.image.single_label_classification,
    )

    # The second step is a model training component. It takes the dataset
    # outputted from the first step, supplies it as an input argument to the
    # component (see `dataset=ds_op.outputs["dataset"]`), and will put its
    # outputs into `training_job_run_op`.
    training_job_run_op = gcc_aip.AutoMLImageTrainingJobRunOp(
        project=project_id,
        display_name="train-antara",
        prediction_type="classification",
        model_type="CLOUD",
        dataset=ds_op.outputs["dataset"],
        model_display_name="train-antara",
        training_fraction_split=0.6,
        validation_fraction_split=0.2,
        test_fraction_split=0.2,
        budget_milli_node_hours=8000,
    )

    # The third and fourth step are for deploying the model.
    create_endpoint_op = gcc_aip.EndpointCreateOp(
        project=project_id,
        display_name = "create-endpoint",
    )

    model_deploy_op = gcc_aip.ModelDeployOp(
        model=training_job_run_op.outputs["model"],
        endpoint=create_endpoint_op.outputs['endpoint'],
        automatic_resources_min_replica_count=1,
        automatic_resources_max_replica_count=1,
    )

from kfp.v2 import compiler
compiler.Compiler().compile(pipeline_func=pipeline,
        package_path='image_classif_pipeline.json')    


import google.cloud.aiplatform as aip

# Before initializing, make sure to set the GOOGLE_APPLICATION_CREDENTIALS
# environment variable to the file path of your service account.
aip.init(
    project=project_id,
    location="us-central1",
)

# Prepare the pipeline job
job = aip.PipelineJob(
    display_name="antara-training",
    template_path="image_classif_pipeline.json",
    pipeline_root=pipeline_root_path,
    parameter_values={
        'project_id': project_id
    }
)

job.submit()
