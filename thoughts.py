"""Contains thoughts in the below doctstring, and potential ideas of interfaces.

Everything should be thought of in the context of a Notebook workflow, i.e. a Python API.

Everything is a "Step", that matches the concept of a ClearML pipeline step.
- Steps accepts inputs (creates depdendencies)
- Steps can be run() either locally or remotely
- Running a step will also entail running its requirements, as needed (or using cached results)
- Steps may store data such as artifacts, etc
- The basic types of steps should be thought of - probably some "data" steps and "model" steps
    > The "data" steps would force a "data" artifact
    > The "model" steps would force a "model" artifact
- This flow creates pipelines by default
- Each step can also output it's configuration maybe?
- Finalizing steps can produce more sophisticated results - i.e. PublishDatasetStep and PublishModelStep, etc.
- Each step should start a Task, need to see about remote execution...


Other implementation details:
- Loading a model: Either via "clearml://" link, a local .zip file, a local .yaml file, or a configuration
- Defining AOI: Current work
- Loading data: ...
"""

"""
Thought: Initialization?
    from ccmlp.init import CCBegin
    
    CCBegin(mlops='clearml', project='my_project_name')  # Reads .env file, clearml.conf, etc?
    
    -> How to send a step for remote execution?
        --> Local data needs to be communicated somehow
        --> Code needs to be wrapped, maybe?
        --> Might have to poll for a task until its completed and return the result, etc?
        
    -> Follow-up:
        -> need to write a run_step.py file and ensure that's the script path (for example, "task.set_script")
        
"""

"""
Thought: Brainstorming examples with Juho
    (imagine the below is a notebook)
    
    from ccmlp.steps import AOIStep, DataFetchingStep, DataTransformationStep, DatasetPublishStep
    
    aoi = AOIStep(inputs=["path/to/file.csv", "clearml://path_to_another_dataset", "aoi_db_definition"])
    aoi.run(queue="default")  # or aoi.run(local=True), etc
    >> runs, prints output of fetched AOI
    
    df_step = DataFetchingStep(inputs=[aoi, "feature_group1", "s3://bucket/path/to/features", feature_definition])
    df_step.run()  # --> will call `aoi.run()` if it was not run before
    
    DataTransformationStep(inputs=[...], transformations=list_of_transformations)  # Transformation code saved in the step 
    
    
    # ----------------------------------------------------------------
    Caching should be done based on e.g. naming conventions, where if a project name + step name match an existing
    step (locally or remotely in ClearML). On a step with dependencies, the dependencies must match too.
    Caching can either be forced (i.e. rename the step), or toggleable (i.e. overwrite=True)
"""




from abc import abstractproperty, abstractclassmethod, abstractmethod, ABC


class IStep(ABC):
    """Mandatory interface for each step"""
    def __init__(self, inputs, **kwargs):
        self.inputs = inputs
        # If any of the inputs are also steps, then we have introduced dependencies
        self.has_dependencies = any([isinstance(inp, IStep) for inp in self.inputs])
        self.completed = False  # Upon initialization, this step was obviously not run yet

    # Each step must implement some _run() function
    @abstractmethod
    def _run(self):
        """Run this specific step"""

    @abstractmethod
    def _post_run(self, run_result):
        """To be used in other "IBaseStep" classes to enforce outputs"""

    def run(self):
        """
        Thought: any *args or **kwargs provided should dictate the flow of execution (i.e. local/remote, or
            forcing rerun of completed steps, etc). They should not affect the *step* itself. Those arguments should
            be provided in the init call.
        """
        for inp in self.inputs:
            if not isinstance(inp, IStep) or inp.completed:
                continue  # No need to rerun, or cannot call `.run()`
            inp.run()
        self._post_run(self._run())  # All inputs in self.inputs are now ready to be used


class IDataStep(IStep, ABC):
    def _post_run(self, run_result):
        """TODO: Store result as a `data` artifact, calculate metadata if needed, etc"""


class IModelStep(IStep, ABC):
    def _post_run(self, run_result):
        """TODO: Store result as a `model` artifact, etc"""

# ----------------------------------------------------------------


class AOIStep(IDataStep):
    """
    Thought: An AOI step can accept many different inputs, and can extract AOI definitions from them.
    Thought: These different inputs can also be formulated as steps (SQLStep?)
    Thought: Examples of source types:
        -> S3 data source (csv or parquet file(s))
        -> SQL data source
        -> ClearML data source
        -> Cells and/or geometries (can extract cells from geometries and build geometries from cells, so this can be an argument)
        Output should be a unified `data` output? <--- This can be embedded into a "IDataStep" class
    """
    def _run(self):
        pass


class ModelValidationStep(IModelStep):
    pass


class ModelTrainingStep(IModelStep):
    pass
