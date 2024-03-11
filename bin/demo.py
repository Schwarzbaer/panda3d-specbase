from panda3d.core import Vec4

from specbase import SpecBase
from specbase import load_model, refov
from specbase import RendererElement
from specbase import SBWindow, SBSceneGraph, SBCamera, SBDisplayRegion, SBKeep


spec = {
    RendererElement.WINDOW: [SBWindow('win')],
    RendererElement.SCENE_GRAPH: [SBSceneGraph('render')],
    RendererElement.CAMERA: [SBCamera('cam')],
    RendererElement.DISPLAY_REGION: [SBDisplayRegion('win_dr3d', 'win', 'cam', dimensions=Vec4(0.0, 0.5, 0.0, 1.0))],
}
SpecBase(spec)


base.cam.reparent_to(base.render)
base.cam.set_y(-10)
refov(base.cam, base.win)
model = load_model("models/smiley")
model.reparent_to(base.render)

base.step()

new_spec = {
    RendererElement.WINDOW: [SBKeep('win'), SBWindow('win_2')],
    RendererElement.SCENE_GRAPH: [SBKeep('render')],
    RendererElement.CAMERA: [SBKeep('cam'), SBCamera('cam_2')],
    RendererElement.DISPLAY_REGION: [SBKeep('win_dr3d'), SBDisplayRegion('win_dr3d_2', 'win_2', 'cam_2', dimensions=Vec4(0.5, 1.0, 0.0, 1.0))],
}
base.respec(new_spec)
base.cam_2.reparent_to(base.render)
base.cam_2.set_h(45)
base.cam_2.set_y(base.cam_2, -10)
refov(base.cam_2, base.win)

base.step()

new_spec = {
    RendererElement.WINDOW: [SBKeep('win_2')],
    RendererElement.SCENE_GRAPH: [SBKeep('render')],
    RendererElement.CAMERA: [SBKeep('cam_2')],
    RendererElement.DISPLAY_REGION: [SBKeep('win_dr3d_2')],
}
base.respec(new_spec)


base.run()
