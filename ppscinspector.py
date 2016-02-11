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
from __future__ import print_function
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

    def __init__(self, image, img_data, sources, poslist, index=0, **kwargs):
        PanZoomCamera.__init__(self, **kwargs)
        self.index = index
        self.image = image
        self.img_data = img_data
        self.sources = sources
        self.poslist = poslist
        self.nsrc = len(poslist)
        self._keymap = {
            keys.UP: +1,
            keys.DOWN: -1,
            keys.LEFT: -1,
            keys.RIGHT: +1,
            keys.SPACE: +1
        }
        self._timer = Timer(0.2, start=False, connect=self.on_timer)

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
        imin, imax = np.nanpercentile(imsect, [5.0, 99.0])
        #cmin = -0.01 + 1.2*self.sources['background'][self.sources.index==self.index].values[0]
        smax = 1.2*self.sources['susflux'][self.sources.index==self.index].values[0]/1000.0 + imin
        #print(imin,imax,smax)
        self.image.set_data(bytescale(self.img_data,
                     cmin=imin, cmax=smax))
        # add a label (take out 'cause this kills the performance)
        #txt = scene.visuals.Text('sourceid {}'.format(self.sources['sourceid'][self.index]),
        #     parent=self.viewbox, font_size=14, color='green',
        #     anchor_x='left', anchor_y='top')
        #txt.pos = 10, 10
        #rect = scene.visuals.Rectangle(height=40, width=100, color='black',
        #          parent=self.viewbox)
        #rect.pos = 10,10
        #rect.update()
        #txt.update()

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

        if event.type == 'key_press':
            if event.key in self._keymap:
                val = self._keymap[event.key]
                self.update_index(val)
                self.update_pan()
                self.view_changed()

            elif event.key == 'M':
                self._timer.start()

            elif event.key == 'S':
                self._timer.stop()

            #elif event.key == 'X':
            #    ind = np.argsort(self.poslist[:,0])
            #    self.poslist = self.poslist[ind]

            #elif event.key == 'Y':
            #    ind = np.argsort(self.poslist[:,1])
            #    self.poslist = self.poslist[ind]

            elif event.key == 'L':
                print(self.sources[self.sources.sourceid==self.sources['sourceid'][self.index]])

def find_map(obsid, band, mapdir, template="{}_PACS_L25_HPPJSMAP{}_SPGv13.0.0.fits.gz"):
    """ Walk the map directory and return the map data and marker size
	1342186121_PACS_L25_HPPJSMAPB_SPGv12.1.0.fits
    Parameters:
    -----------
    obsid (int): observation id (10-digit integer)
    band (string) : blue, green or red
    mapdir (string) : top-level of map directory
    template (string) : how to format obsid and band into a map name

    Returns:
    --------
    img_data : numpy array of image data
    mrkr_size : size of markers in pixels
    wcs : astropy.wcs object for the image
    """
    if (band == 'blue') | (band == 'green'):
     filter = 'B'
    else:
     filter = 'R'
    fname = template.format(obsid, filter)
    print,filter
    fullname = fname
    for root, dir, files in os.walk(os.path.expanduser(mapdir), followlinks=True):
        for name in files:
            if name.endswith(fname):
                fullname = os.path.join(root, fname)
                break
            elif name.endswith(fname.replace('L25','L3')):
                fullname = os.path.join(root, fname.replace('L25','L3'))
                break
    # Get the data
    hdu = fits.open(fullname)
    img_data = hdu[1].data
    #del hdu[1].header['CUNIT1']
    #del hdu[1].header['CUNIT2']
    img_wcs = WCS(hdu[1].header)
    deg_per_pix = np.sqrt(np.abs(np.linalg.det(img_wcs.pixel_scale_matrix)))
    beams = {'blue':5.5, 'green':7.0, 'red':11.5}
    beam_size = beams[band]/3600.
    mrkr_size = beam_size/deg_per_pix
    return(img_data, mrkr_size, img_wcs)

def sourcelist_pscdb(obsid, band):
    """ Return dataframe from source table

    Parameters:
    -----------
    obsid (int): observation id (10-digit integer)
    band (string) : blue, green or red

    Returns:
    --------
    sources : Pandas dataframe of the sources
    """
    import psycopg2 as pg
    import pandas.io.sql as psql
    with pg.connect("dbname=pacs") as connection:
        sources = psql.read_sql("""
            select sourceid, obsid, band, susra,susdec,daora,daodec,centerrafit,centerdecfit,susflux
            from source
            where obsid={} and band='{}'
            order by sourceid asc""".format(obsid, band),
            connection)
    return(sources)

def display_sources(sources, img_data, mrkr_size, wcs, cmap='grays',
        susscolor="blue", tmlcolor="green", tm2color="orange",
        titlestring="PACS PSC"):
    """
    display sources overlaid on image

    Parameters:
    -----------
    sources : dataframe including ra and dec values
    img_data : numpy array of the image
    mrkr_size : diameter of the markers in pixel units
    wcs : astropy.wcs wcs object for the image (to convert ra,dec to pixels)
    cmap : vispy color map, defaults to 'grays'. See vispy.colors.get_colormaps()

    Returns:
    --------
    None
    """
    nsrc = len(sources)

    sworld = np.vstack([sources['susra'].values,sources['susdec'].values]).T

    pos = wcs.wcs_world2pix(sworld,0) + 0.5

    keydict = dict(escape='close', p=lambda x: max(0,i-1),
        n=lambda x: min(nsrc,i+1))

    #canvas = scene.SceneCanvas(keys=keydict)
    canvas = scene.SceneCanvas(keys='interactive')
    canvas.size = img_data.shape
    canvas.title = titlestring
    canvas.show()

    # Set viewbox to display the image with interactive pan/zoom
    view = canvas.central_widget.add_view()

    # Create the image
    #image = scene.visuals.Image(bytescale(img_data, cmin=0.8*np.nanmin(img_data),
    #     cmax=1.05*np.nanmax(img_data)), parent=view.scene)
    # note that vispy.color.get_colormaps() returns all the ColorMaps
    image = scene.visuals.Image(bytescale(img_data, cmin=0.9*np.nanmin(img_data),
                                      cmax=1.02*np.nanmax(img_data)),
                            #clim=(0.8*np.nanmin(img_data), 1.05*np.nanmax(img_data)),
                            cmap=cmap,
                            parent=view.scene)
    # Set 2D camera (the camera will scale to the contents in the scene)
    view.camera = SourceInspectCamera(image,img_data,sources,pos,index=0,aspect=1)
    view.camera.set_range()
    # Add the markers
    if (susscolor != None):
        p1 = scene.visuals.Markers(parent=view.scene)
        p1.set_data(pos,
             face_color=None, edge_color=susscolor, scaling=True,
             edge_width=2.0, size=mrkr_size)
    if (tmlcolor != None):
        tmlworld = np.vstack([sources['susra'].values,sources['susdec'].values]).T
        postml = wcs.wcs_world2pix(tmlworld,0) + 0.5
        p2 = scene.visuals.Markers(parent=view.scene)
        p2.set_data(postml,
             face_color=None, edge_color=tmlcolor, scaling=True,
             edge_width=1.5, size=mrkr_size)
    if (tm2color != None):
        tm2world = np.vstack([sources['centerrafit'].values,sources['centerdecfit'].values]).T
        postm2 = wcs.wcs_world2pix(tm2world,0) + 0.5
        p3 = scene.visuals.Markers(parent=view.scene)
        p3.set_data(postm2,
             face_color=None, edge_color=tm2color, scaling=True,
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
    band = args.array
    mapdir = args.mapdir
    print('loading sources from database for {} {}...'.format(obsid,band), end='')
    sources = sourcelist_pscdb(obsid, band)
    print('done.')
    img_data, mrkr_size, wcs = find_map(obsid, band, mapdir)
    titlestring = "SPSC: {} {}".format(obsid, band)
    display_sources(sources, img_data, mrkr_size, wcs, titlestring=titlestring)
