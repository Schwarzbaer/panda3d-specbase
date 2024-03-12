from panda3d.core import Vec4

from specbase import SpecBase
from specbase import SBWindow, SBSceneGraph, SBCamera, SBDisplayRegion
from specbase import load_model, refov


first_spec = [
    SBWindow('win'),
    SBSceneGraph('render'),
    SBCamera('cam'),
    SBDisplayRegion('win_dr3d', 'win', 'cam', dimensions=Vec4(0.0, 0.5, 0.0, 1.0))
]
SpecBase(first_spec)

# Now that the renderer exists, we can set up the scene.
base.cam.reparent_to(base.render)
base.cam.set_y(-10)
refov(base.cam, base.win)
model = load_model("models/smiley")
model.reparent_to(base.render)
base.step()  # Let's render what's there already.

# We can change the spec at runtime by providing the intended state.
second_spec = first_spec + [
    SBWindow('win_2'),
    SBCamera('cam_2'),
    SBDisplayRegion('win_dr3d_2', 'win_2', 'cam_2', dimensions=Vec4(0.5, 1.0, 0.0, 1.0)),
]

base.respec(second_spec)


base.cam_2.reparent_to(base.render)
base.cam_2.set_h(45)
base.cam_2.set_y(base.cam_2, -10)
refov(base.cam_2, base.win)
base.step()


# Let's close the first window.
third_spec = [
    SBWindow('win_2'),
    SBSceneGraph('render'),
    SBCamera('cam_2'),
    SBDisplayRegion('win_dr3d_2'),
]
base.respec(third_spec)


base.run()
