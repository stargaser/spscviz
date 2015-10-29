#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vispy: gallery 30
# -----------------------------------------------------------------------------
# Copyright (c) 2015, California Institute of Technology.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
"""
Simple use of SceneCanvas to display an Image.
"""
import sys
import os
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

    def __init__(self, image, img_data, poslist, index=0, **kwargs):
        PanZoomCamera.__init__(self, **kwargs)
        self.index = index
        self.image = image
        self.img_data = img_data
        self.poslist = poslist
        self.nsrc = len(poslist)
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
        newX = self.poslist[self.index][0]
        newY = self.poslist[self.index][1]
        curX = self.rect.left + self.rect.width/2.0
        curY = self.rect.bottom + self.rect.height/2.0
        self.pan((newX-curX,newY-curY))
        # update image data
        imsect = self.img_data[int(self.rect.bottom):int(self.rect.top),
               int(self.rect.left):int(self.rect.right)]
        self.image.set_data(bytescale(img_data,cmin=0.8*np.nanmin(imsect),
                       cmax=1.02*np.nanmax(imsect)))

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

        if event.key == 'X':
            ind = np.argsort(self.poslist[:,0])
            self.poslist = self.poslist[ind]

        if event.key == 'Y':
            ind = np.argsort(self.poslist[:,1])
            self.poslist = self.poslist[ind]

def find_map(obsid, arrayname, mapdir, template="{}{}_map.fits.zip"):
    """ Walk the map directory and return the map data and marker size

    Parameters:
    -----------
    obsid (int): observation id (10-digit integer)
    arrayname (string) : PSW, PMW or PLW
    mapdir (string) : top-level of map directory
    template (string) : how to format obsid and arrayname into a map name

    Returns:
    --------
    img_data : numpy array of image data
    mrkr_size : size of markers in pixels
    """
    fname = template.format(obsid, arrayname)
    fullname = fname
    for root, dir, files in os.walk(os.path.abspath(mapdir), followlinks=True):
        for name in files:
            if name.endswith(fname):
                fullname = os.path.join(root, fname)
                break
            elif name.endswith(fname.replace('map','pmd')):
                fullname = os.path.join(root, fname.replace('map','pmd'))
                break
    # Get the data
    hdu = fits.open(fullname)
    img_data = hdu[1].data
    img_wcs = WCS(hdu[1].header)
    deg_per_pix = np.sqrt(np.abs(np.linalg.det(img_wcs.pixel_scale_matrix)))
    beams = {'PSW':17.0, 'PMW':32.0, 'PLW':42.0}
    beam_size = beams[arrayname]/3600.
    mrkr_size = beam_size/deg_per_pix
    return(img_data, mrkr_size)

def sourcelist_pscdb(obsid, arrayname):
    """ Return dataframe from source table

    Parameters:
    -----------
    obsid (int): observation id (10-digit integer)
    arrayname (string) : PSW, PMW or PLW

    Returns:
    --------
    sources : Pandas dataframe of the sources
    """
    import psycopg2 as pg
    import pandas.io.sql as psql
    with pg.connect("dbname=spire user=spire host=psc.ipac.caltech.edu") as connection:
        sources = psql.read_sql("""
            select sourceid, obsid, arrayname, x, y
            from source
            where obsid={} and arrayname='{}'""".format(obsid, arrayname),
            connection)
    return(sources)

def display_sources(sources, img_data, mrkr_size):
    nsrc = len(sources)

    pos = np.vstack([sources['x'].data, sources['y'].data]).T
    print(pos.shape)

    keydict = dict(escape='close', p=lambda x: max(0,i-1),
        n=lambda x: min(nsrc,i+1))

    canvas = scene.SceneCanvas(keys=keydict)
    canvas.size = img_data.shape
    canvas.show()

    # Set up a viewbox to display the image with interactive pan/zoom
    view = canvas.central_widget.add_view()

    # Create the image
    #image = scene.visuals.Image(bytescale(img_data, cmin=0.8*np.nanmin(img_data),
    #     cmax=1.05*np.nanmax(img_data)), parent=view.scene)
    # note that vispy.color.get_colormaps() returns all the ColorMaps
    image = scene.visuals.Image(bytescale(img_data, cmin=0.9*np.nanmin(img_data),
                                      cmax=1.02*np.nanmax(img_data)),
                            #clim=(0.8*np.nanmin(img_data), 1.05*np.nanmax(img_data)),
                            cmap='grays',
                            parent=view.scene)
    # Set 2D camera (the camera will scale to the contents in the scene)
    view.camera = SourceInspectCamera(image,img_data,pos,index=0,aspect=1)
    view.camera.set_range()
    # Add the markers
    p1 = scene.visuals.Markers(parent=view.scene)
    p1.set_data(pos,
             face_color=None, edge_color="white", scaling=True,
             edge_width=1.5, size=mrkr_size)
    app.run()
    return


if __name__ == '__main__' and sys.flags.interactive == 0:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("obsid", help="observation id", type=int)
    parser.add_argument("array", help="SPIRE array name, must be PSW, PMW or PMW")
    parser.add_argument("mapdir", help="top-level map directory")
    args = parser.parse_args()
    obsid = args.obsid
    arrayname = args.array
    mapdir = args.mapdir
    sources = sourcelist_pscdb(obsid, arrayname)
    img_data, mrkr_size = find_map(obsid, arrayname, mapdir)
    display_sources(sources, img_data, mrkr_size)
