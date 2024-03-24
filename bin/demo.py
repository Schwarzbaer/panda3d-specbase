from panda3d.core import Vec4

from specbase import SpecBase
from specbase import (
    SBPipe,
    SBEngine,
    SBWindow,
    SBSceneGraph,
    SBCamera,
    SBDisplayRegion,
)
from specbase import refov
from specbase.debased import render_frame
from specbase.debased import render_frame_task


first_spec = [
    SBPipe('pipe'),
    SBEngine('engine', 'pipe'),
    SBWindow('win', 'pipe'),
    SBSceneGraph('render'),
    SBCamera('cam'),
    SBDisplayRegion('win_dr3d', 'win', 'cam', dimensions=Vec4(0.0, 0.5, 0.0, 1.0))
]
SpecBase(first_spec)

# Now that the renderer exists, we can set up the scene.
base.cam.reparent_to(base.render)
base.cam.set_y(-10)
refov(base.cam, base.win)
model = base.loader.load_model("models/smiley")
model.reparent_to(base.render)
render_frame(base.engine)  # Let's render what's there already.

# We can change the spec at runtime by providing the intended state.
second_spec = first_spec + [
    SBWindow('win_2', 'pipe'),
    SBCamera('cam_2'),
    SBDisplayRegion('win_dr3d_2', 'win_2', 'cam_2', dimensions=Vec4(0.5, 1.0, 0.0, 1.0)),
]

base.respec(second_spec)


base.cam_2.reparent_to(base.render)
base.cam_2.set_h(45)
base.cam_2.set_y(base.cam_2, -10)
refov(base.cam_2, base.win)
render_frame(base.engine)


# Let's close the first window.
third_spec = [
    SBPipe('pipe'),
    SBEngine('engine', 'pipe'),
    SBWindow('win_2'),
    SBSceneGraph('render'),
    SBCamera('cam_2'),
    SBDisplayRegion('win_dr3d_2'),
]
base.respec(third_spec)

base.task_mgr.add(render_frame_task(base.engine))
base.run()
