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


class RendererElement(enum.Enum):
    WINDOW = 1
    SCENE_GRAPH = 2
    CAMERA = 3
    DISPLAY_REGION = 4


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
        self._setup = {
            RendererElement.WINDOW: {},
            RendererElement.SCENE_GRAPH: {},
            RendererElement.CAMERA: {},
            RendererElement.DISPLAY_REGION: {},
        }
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
        sb_element_types_forward = [
            RendererElement.WINDOW,
            RendererElement.SCENE_GRAPH,
            RendererElement.CAMERA,
            RendererElement.DISPLAY_REGION,
        ]
        next_state_elements = {et: [] for et in sb_element_types_forward}
        for sb_element_type in sb_element_types_forward:
            for sb_element in spec[sb_element_type]:
                element_name = sb_element.name
                next_state_elements[sb_element_type].append(element_name)
                if isinstance(sb_element, SBKeep):
                    continue
                if element_name not in self._setup[sb_element_type]:
                    new_element = self.add_element(sb_element)
                    self._setup[sb_element_type][element_name] = new_element
                    if sb_element.add_to_base:
                        setattr(self, element_name, new_element)

        sb_element_types_backward = [
            RendererElement.DISPLAY_REGION,
            RendererElement.CAMERA,
            RendererElement.SCENE_GRAPH,
            RendererElement.WINDOW,
        ]
        nodes_to_delete = []
        for sb_element_type in sb_element_types_backward:
            for name in self._setup[sb_element_type]:
                if name not in next_state_elements[sb_element_type]:
                    nodes_to_delete.append((sb_element_type, name))
        for sb_element_type, name in nodes_to_delete:
            self.del_element(sb_element_type, name)

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

    def del_element(self, sb_element_type, name):
        if sb_element_type == RendererElement.WINDOW:
            self.del_window(name)
        elif sb_element_type == RendererElement.SCENE_GRAPH:
            self.del_scene_graph(name)
        elif sb_element_type == RendererElement.CAMERA:
            self.del_camera(name)
        elif sb_element_type == RendererElement.DISPLAY_REGION:
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
        win = self._setup[RendererElement.WINDOW][name]
        base.engine.remove_window(win)

    def add_scene_graph(self, sb_element):
        sg_name = sb_element.name
        np = NodePath(sg_name)
        return np

    def del_scene_graph(self, name):
        sg = self._setup[RendererElement.SCENE_GRAPH][name]
        sg.remove_node()
        del self._setup[RendererElement.SCENE_GRAPH][name]

    def add_camera(self, sb_element):
        cam_name = sb_element.name
        camera = Camera(cam_name)
        camera_np = NodePath(camera)
        return camera_np

    def del_camera(self, name):
        cam = self._setup[RendererElement.CAMERA][name]
        cam.remove_node()
        del self._setup[RendererElement.CAMERA][name]

    def add_display_region(self, sb_element):
        dr_name = sb_element.name
        win_name = sb_element.window_name
        cam_name = sb_element.camera_name
        win = self._setup[RendererElement.WINDOW][win_name]
        cam = self._setup[RendererElement.CAMERA][cam_name]
        dr = win.make_display_region()
        dr.set_camera(cam)
        if sb_element.dimensions is not None:
            dr.dimensions = sb_element.dimensions
        return dr

    def del_display_region(self, name):
        dr = self._setup[RendererElement.DISPLAY_REGION][name]
        dr.window.remove_display_region(dr)


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
    def __init__(self, name, window_name, camera_name, dimensions=None, add_to_base=True):
        self.name = name
        self.window_name = window_name
        self.camera_name = camera_name
        self.dimensions = dimensions
        self.add_to_base = add_to_base


class SBKeep:
    def __init__(self, name):
        self.name = name


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
