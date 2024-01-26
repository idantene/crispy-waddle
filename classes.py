def run_step(*args, **kwargs):
    from clearml import Task
    import pickle
    from pathlib import Path

    task = Task.current_task()
    instance = task.artifacts['inputs/self'].get()
    if isinstance(instance, Path):
        # instance might be a posix path to a pickled file
        try:
            with open(instance) as f:
                instance = pickle.load(f)
        except UnicodeDecodeError:
            with open(instance, "rb") as f:
                instance = pickle.load(f)
    return instance.run(*args, **kwargs)


class TestStep:

    def __init__(self, foo=None):
        self.foo = foo

    def _run(self, **kwargs):
        print(kwargs)
        print(self.foo)
        return self.foo

    # TODO: Make a wrapper
    def create_task(self, project_name, queue=None):
        import os
        import clearml
        import dill

        with open("run_step.py", "w") as f:
            # TODO: What about additional helper functions etc?
            f.write("from clearml import Task\n")
            f.write(dill.source.getsource(self.__class__))
            f.write(dill.source.getsource(run_step))
            f.write("\n\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    task = Task.init()\n")
            f.write("    kwargs = dict()\n")
            f.write("    task.connect(kwargs, name='kwargs')\n")
            f.write("    run_step(**kwargs)")

        with open("run_step.py") as f:
            diff = f.read()

        suffix_no = 0
        while True:
            try:
                suffix = "" if not suffix_no else f"_{suffix_no}"
                task = clearml.Task.create(project_name=project_name, task_name=self.__class__.__name__ + suffix,
                                           script="run_step.py", add_task_init_call=False, packages=True)
                break
            except ValueError as e:
                print(e)
                if not suffix_no:
                    suffix_no = 1
                suffix_no += 1
        task.upload_artifact('inputs/self', self, wait_on_upload=True)

        task.update_task(task_data={
            'script': task.data.script.to_dict().update(
                {'entry_point': "run_step.py", 'working_dir': '.', 'diff': diff})})

        if queue is not None:
            clearml.Task.enqueue(task, queue_name=queue)
        os.unlink("run_step.py")

        return task
