import enum

from panda3d.core import AsyncTaskManager
from panda3d.core import GraphicsEngine
from panda3d.core import GraphicsPipeSelection
from panda3d.core import FrameBufferProperties
from panda3d.core import WindowProperties
from panda3d.core import GraphicsPipe
from panda3d.core import NodePath
from panda3d.core import Camera
from panda3d.core import Filename

from direct.showbase import Loader


default_flags = GraphicsPipe.BF_fb_props_optional


class SBPipe:
    def __init__(self, name, pipe_name=None, add_to_base=True):
        self.name = name
        self.pipe_name = pipe_name
        self.add_to_base = add_to_base


class SBEngine:
    def __init__(self, name, pipe=None, add_to_base=True):
        self.name = name
        self.pipe = pipe
        self.add_to_base = add_to_base


class SBWindow:
    def __init__(self, name, pipe=None, sort=0, fb_props=None, win_props=None, flags=default_flags, add_to_base=True):
        self.name = name
        self.pipe = pipe
        self.sort = sort
        if fb_props is None:
            self.fb_props = FrameBufferProperties.getDefault()
        else:
            self.fb_props = fb_props
        if win_props is None:
            self.win_props = WindowProperties.getDefault()
        else:
            self.win_props = win_props
        self.flags = flags
        self.add_to_base = add_to_base


class SBSceneGraph:
    def __init__(self, name, add_to_base=True):
        self.name = name
        self.add_to_base = add_to_base


class SBCamera:
    def __init__(self, name, add_to_base=True):
        self.name = name
        self.add_to_base = add_to_base


class SBDisplayRegion:
    def __init__(self, name, window_name=None, camera_name=None, dimensions=None, add_to_base=True):
        self.name = name
        self.window_name = window_name
        self.camera_name = camera_name
        self.dimensions = dimensions
        self.add_to_base = add_to_base


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
        from direct.task.TaskManagerGlobal import taskMgr
        self.task_mgr = taskMgr

    def run(self) -> None: # pylint: disable=method-hidden
        self.task_mgr.run()


# class NoTaskMgrBase:
#     def step(self):
#         self.engine.render_frame()
#         self.engine.flip_frame()
#  
#     def run(self):
#         while True:
#             self.step()


class SpecBase(LoaderBase, TaskManagerBase):
    def __init__(self, spec=None, task_mgr=True, base=True):
        LoaderBase.__init__(self)
        if task_mgr:
            TaskManagerBase.__init__(self)

        self._setup = {}
        if base:
            __builtins__["base"] = self

        self.type_to_func = {
            SBPipe: (self.add_pipe, self.del_pipe),
            SBEngine: (self.add_engine, self.del_engine),
            SBWindow: (self.add_window, self.del_window),
            SBSceneGraph: (self.add_scene_graph, self.del_scene_graph),
            SBCamera: (self.add_camera, self.del_camera),
            SBDisplayRegion: (self.add_display_region, self.del_display_region),
        }
        if spec is not None:
            self.respec(spec)

    def respec(self, spec):
        creation_order = [
            SBPipe,
            SBEngine,
            SBWindow,
            SBSceneGraph,
            SBCamera,
            SBDisplayRegion,
        ]
        for sb_element_type in creation_order:
            for sb_element in [elem for elem in spec if isinstance(elem, sb_element_type)]:
                self.process_for_addition(sb_element)

        next_state_names = set([elem.name for elem in spec])
        current_state_names = set(self._setup.keys())
        obsolete_names = current_state_names - next_state_names
        obsolete_states = [self._setup[name][0] for name in obsolete_names]
        for sb_element_type in reversed(creation_order):
            for sb_element in [elem for elem in obsolete_states if isinstance(elem, sb_element_type)]:
                self.process_for_deletion(sb_element)

    def process_for_addition(self, sb_element):
        element_name = sb_element.name
        # If it exists already, skip it.
        if element_name in self._setup:
            return
        # It doesn't, so create it.
        new_element = self.add_element(sb_element)
        self._setup[element_name] = (sb_element, new_element)
        if sb_element.add_to_base:
            setattr(self, element_name, new_element)

    def process_for_deletion(self, sb_element):
        # We need to delete the object itself, its _setup entry, and the
        # `base` attribute.
        sb_element, _ = self._setup[sb_element.name]

        self.del_element(sb_element)
        if sb_element.add_to_base:
            delattr(self, sb_element.name)
        del self._setup[sb_element.name]

    def add_element(self, sb_element):
        add_func, _ = self.type_to_func[type(sb_element)]
        return add_func(sb_element)

    def del_element(self, sb_element):
        name = sb_element.name
        _, del_func = self.type_to_func[type(sb_element)]
        del_func(name)

    def add_pipe(self, sb_pipe):
        available_pipes = GraphicsPipeSelection.get_global_ptr()
        if sb_pipe.pipe_name is None:
            pipe = available_pipes.make_default_pipe()
        else:
            pipe = available_pipes.make_module_pipe(sb_pipe.name)
        return pipe

    def del_pipe(self, name):
        print(f"Pipe '{name}' will be removed when it falls out of scope.")

    def add_engine(self, sb_engine):
        if sb_engine.pipe is None:
            engine = GraphicsEngine.get_global_ptr()
        else:
            _, pipe = self._setup[sb_engine.pipe]
            engine = GraphicsEngine(pipe)
        return engine

    def del_engine(self, name):
        print(f"Engine '{name}' will be removed when it falls out of scope.")

    def add_window(self, sb_window):
        _, pipe = self._setup[sb_window.pipe]
        window = self.engine.make_output(
            pipe,
            sb_window.name,
            sb_window.sort,
            sb_window.fb_props,
            sb_window.win_props,
            sb_window.flags,
        )
        if window is None:
            raise Exception(f"Couldn't create window '{sb_window.name}'")
        return window

    def del_window(self, name):
        _, win = self._setup[name]
        base.engine.remove_window(win)

    def add_scene_graph(self, sb_element):
        sg_name = sb_element.name
        np = NodePath(sg_name)
        return np

    def del_scene_graph(self, name):
        _, sg = self._setup[name]
        sg.remove_node()

    def add_camera(self, sb_element):
        cam_name = sb_element.name
        camera = Camera(cam_name)
        camera_np = NodePath(camera)
        return camera_np

    def del_camera(self, name):
        _, cam = self._setup[name]
        cam.remove_node()

    def add_display_region(self, sb_element):
        dr_name = sb_element.name
        win_name = sb_element.window_name
        cam_name = sb_element.camera_name
        _, win = self._setup[win_name]
        _, cam = self._setup[cam_name]
        dr = win.make_display_region()
        dr.set_camera(cam)
        if sb_element.dimensions is not None:
            dr.dimensions = sb_element.dimensions
        return dr

    def del_display_region(self, name):
        _, dr = self._setup[name]
        dr.window.remove_display_region(dr)


def refov(camera, window):
    camera.node().get_lens().set_aspect_ratio(
        float(window.get_x_size()) /
        float(window.get_y_size())
    )
