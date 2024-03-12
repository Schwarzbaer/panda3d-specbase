import enum

from panda3d.core import AsyncTaskManager
from panda3d.core import GraphicsEngine
from panda3d.core import GraphicsPipeSelection
from panda3d.core import Loader
from panda3d.core import FrameBufferProperties
from panda3d.core import WindowProperties
from panda3d.core import GraphicsPipe
from panda3d.core import NodePath
from panda3d.core import Camera
from panda3d.core import LoaderOptions
from panda3d.core import Filename


class SBWindow:
    def __init__(self, name, add_to_base=True):
        self.name = name
        self.add_to_base = add_to_base
        self.fbprops = FrameBufferProperties.getDefault()
        self.wprops = WindowProperties.getDefault()
        self.flags = GraphicsPipe.BFFbPropsOptional | GraphicsPipe.BFRequireWindow
        self.sort = 0


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


class SpecBase:
    def __init__(self, spec=None, pipe=None, task_mgr=True, base=True):
        if task_mgr:
            self.task_mgr = AsyncTaskManager.get_global_ptr()
        self.engine = GraphicsEngine.get_global_ptr()

        available_pipes = GraphicsPipeSelection.get_global_ptr()
        available_pipes.print_pipe_types()
        if pipe is None:
            self.pipe = available_pipes.make_default_pipe()
        else:
            self.pipe = available_pipes.make_module_pipe(pipe)
        self.loader = Loader.getGlobalPtr()
        self._setup = {}
        if base:
            __builtins__["base"] = self
        if spec is not None:
            self.respec(spec)

    def step(self):
        self.engine.render_frame()
        self.engine.flip_frame()

    def run(self):
        while True:
            self.step()

    def respec(self, spec):
        # First, we add all new elements *except* DisplayRegions, and
        # then those too.
        for sb_element in [elem for elem in spec if not isinstance(elem, SBDisplayRegion)]:
            self.process_for_addition(sb_element)
        for sb_element in [elem for elem in spec if isinstance(elem, SBDisplayRegion)]:
            self.process_for_addition(sb_element)

        next_state_names = set([elem.name for elem in spec])
        current_state_names = set(self._setup.keys())
        obsolete_names = current_state_names - next_state_names
        obsolete_states = [self._setup[name][0] for name in obsolete_names]
        for sb_element in [elem for elem in obsolete_states if isinstance(elem, SBDisplayRegion)]:
            self.process_for_deletion(sb_element)
        for sb_element in [elem for elem in obsolete_states if not isinstance(elem, SBDisplayRegion)]:
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
        if isinstance(sb_element, SBWindow):
            return self.add_window(sb_element)
        elif isinstance(sb_element, SBSceneGraph):
            return self.add_scene_graph(sb_element)
        elif isinstance(sb_element, SBCamera):
            return self.add_camera(sb_element)
        elif isinstance(sb_element, SBDisplayRegion):
            return self.add_display_region(sb_element)
        else:
            raise ValueError(f"Unknown element type {type(sb_element)} for name {sb_element.name}")

    def del_element(self, sb_element):
        name = sb_element.name
        if isinstance(sb_element, SBWindow):
            self.del_window(name)
        elif isinstance(sb_element, SBSceneGraph):
            self.del_scene_graph(name)
        elif isinstance(sb_element, SBCamera):
            self.del_camera(name)
        elif isinstance(sb_element, SBDisplayRegion):
            self.del_display_region(name)
        else:
            raise ValueError(f"Unknown element type {sb_element_type}")

    def add_window(self, sb_window):
        window = self.engine.make_output(
            self.pipe,
            sb_window.name,
            sb_window.sort,
            sb_window.fbprops,
            sb_window.wprops,
            sb_window.flags,
        )
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


def load_model(name):
    loader_options = LoaderOptions()
    model = base.loader.load_sync(
        Filename("models/smiley"),
        loader_options,
    )
    return NodePath(model)


def refov(camera, window):
    camera.node().get_lens().set_aspect_ratio(
        float(window.get_x_size()) /
        float(window.get_y_size())
    )
