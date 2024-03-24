from direct.showbase import Loader


class LoaderBase:
    def __init__(self):
        self.loader = Loader.Loader(self)


def render_frame(graphics_engine):
    graphics_engine.render_frame()
    graphics_engine.flip_frame()


def render_frame_task(graphics_engine):
    def task_func(task):
        render_frame(graphics_engine)
        return task.cont
    return task_func


class TaskManagerBase:
    def __init__(self):
        from direct.task.Task import TaskManager
        self.task_mgr = TaskManager()

    def run(self) -> None: # pylint: disable=method-hidden
        self.task_mgr.run()


class EventBase:
    def __init__(self):
        from direct.showbase.Messenger import Messenger
        self.messenger = Messenger()
