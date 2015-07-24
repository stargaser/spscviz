# -*- coding: utf-8 -*-
# vispy: gallery 30
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
"""
Simple use of SceneCanvas to display an Image.
"""
import sys
from vispy import scene, app, visuals, gloo
from vispy.visuals.transforms import STTransform, TransformSystem
import numpy as np
import astropy.io.fits as fits
from astropy.table import Table
from astropy.wcs import WCS
from scipy.misc import bytescale
from time import sleep
from vispy.geometry import Rect
from vispy.scene import PanZoomCamera
from vispy.util import keys
from vispy.app import Timer

class SourceInspectCamera(PanZoomCamera):
    """
    """

    _state_props = PanZoomCamera._state_props + ('index', )

    def __init__(self, poslist, index=0, **kwargs):
        PanZoomCamera.__init__(self, **kwargs)
        self.index = index
        self.poslist = poslist
        self.nsrc = poslist.shape[0]
        self._keymap = {
            keys.UP: +1,
            keys.DOWN: -1,
            keys.LEFT: -1,
            keys.RIGHT: +1,
            keys.SPACE: +1
        }
        self._timer = Timer(0.1, start=False, connect=self.on_timer)

    @property
    def keymap(self):
        """
        """
        return self._keymap

    def update_index(self, val):
        self.index += val
        if (self.index > self.nsrc-1):
            self.index = 0
        if (self.index < 0):
            self.index = self.nsrc - 1

    def update_pan(self):
        newX, newY = self.poslist[self.index]
        curX = self.rect.left + self.rect.width/2.0
        curY = self.rect.bottom + self.rect.height/2.0
        self.pan((newX-curX,newY-curY))

    def on_timer(self, event):
        """Timer event handler

        Parameters
        ----------
        event : instance of Event
            The event.
        """
        self.update_index(1)
        self.update_pan()
        self.view_changed()

    def viewbox_key_event(self, event):
        """ViewBox key event handler

        Parameters
        ----------
        event : instance of Event
            The event.
        """
        PanZoomCamera.viewbox_key_event(self, event)
        if event.handled or not self.interactive:
            return

        if event.key in self._keymap:
            val = self._keymap[event.key]
            self.update_index(val)
            self.update_pan()
            self.view_changed()

        if event.key == 'M':
            self._timer.start()

        if event.key == 'S':
            self._timer.stop()

# Get the data
img_data = fits.getdata('/Users/shupe/data/spsc/level2/twop3_02/1342255106PSW_map.fits.zip', ext=1)

# Get the source list
sources = Table.read('/Users/shupe/Analysis/spire_psc/vispy/1342255106PSW_map_detect.fits', hdu=1)

pos = np.vstack([sources['x'],sources['y']]).T + 0.5
nsrc = pos.shape[0]
i = 0

keydict = dict(escape='close', p=lambda x: max(0,i-1),
    n=lambda x: min(nsrc,i+1))

canvas = scene.SceneCanvas(keys=keydict)
canvas.size = img_data.shape
canvas.show()

# Set up a viewbox to display the image with interactive pan/zoom
view = canvas.central_widget.add_view()

# Create the image
image = scene.visuals.Image(bytescale(img_data, cmin=0.8*np.nanmin(img_data),
     cmax=1.05*np.nanmax(img_data)), parent=view.scene)



# Set 2D camera (the camera will scale to the contents in the scene)
view.camera = SourceInspectCamera(pos,index=0,aspect=1)

# Add the markers
colors = np.random.uniform(size=(pos.shape[0], 3), low=.5, high=.8)

p1 = scene.visuals.Markers(parent=view.scene)
p1.set_data(pos, face_color=colors)

i=0

#for i in range(pos.shape[0]):
#    view.camera.rect = Rect(pos[i][0],pos[i][1], 20,20)
#    sleep(0.1)
#    canvas.update()


#canvas.tr_sys.visual_to_document = STTransform()
#markers = scene.visuals.Markers()
#colors = np.ones((pos.shape[0], 4), dtype=np.float32)
#markers.set_data(pos, face_color=colors)
#scene.visuals.index=0
#scene.visuals.scale = 1.
#markers.set_symbol(visuals.marker_types[0])
#markers.draw(TransformSystem(canvas))


if __name__ == '__main__' and sys.flags.interactive == 0:
    app.run()
