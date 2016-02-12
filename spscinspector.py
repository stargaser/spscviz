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

is_pacs = False

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
        #self.smin = 0.9*np.nanmin(self.img_data)
        #self.smax = 1.02*np.nanmax(self.img_data)
        self.smin, self.smax = np.nanpercentile(self.img_data, [5.0, 99.0])
        self.accelerator = 5.0
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
        self.smin = imin
        #cmin = -0.01 + 1.2*self.sources['background'][self.sources.index==self.index].values[0]
        if (is_pacs):
            self.smax = 1.2*self.sources['susflux']\
                  [self.sources.index==self.index].values[0]/1000.0/10.0 + imin
        else:
            self.smax = 1.2*self.sources['fluxtml']\
                  [self.sources.index==self.index].values[0]/1000.0 + imin
        self.update_scale()
        
    def update_scale(self):
        self.image.set_data(bytescale(self.img_data, cmin=self.smin, cmax=self.smax))
        self.view_changed()

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
                
            elif event.key == 'T':
                sdiff = self.accelerator*(self.smax - self.smin)/255.0
                self.smax += sdiff
                self.smin += sdiff
                self.update_scale()
            
            elif event.key == 'B':
                sdiff = self.accelerator*(self.smax - self.smin)/255.0
                self.smax -= sdiff
                self.smin -= sdiff
                self.update_scale()
                
            elif event.key == 'N':
                sdiff = self.accelerator*(self.smax - self.smin)/255.0
                self.smax -= sdiff
                self.smin += sdiff
                self.update_scale()
                
            elif event.key == 'W':
                sdiff = self.accelerator*(self.smax - self.smin)/255.0
                self.smax += sdiff
                self.smin -= sdiff
                self.update_scale()
                
            elif event.key == 'U':
                print("Current stretch limits: %10.4g, %10.4g"%(self.smin, self.smax))
                self.smin = float(input("New lower value?"))
                self.smax = float(input("New upper value?"))
                self.update_scale()

def find_map(obsid, band, mapdir, template="{}{}_map.fits.zip"):
    """ Walk the map directory and return the map data and marker size

    Parameters:
    -----------
    obsid (int): observation id (10-digit integer)
    band (string) : blue, green, red, PSW, PMW or PLW
    mapdir (string) : top-level of map directory
    template (string) : how to format obsid and filter into a map name

    Returns:
    --------
    img_data : numpy array of image data
    filter : 'blue', 'green', 'red' for PACS, 'PSW', 'PMW', 'PSW' for SPIRE
    mrkr_size : size of markers in pixels
    wcs : astropy.wcs object for the image
    """
    fname = template.format(obsid, band)
    fullname = fname
    for root, dir, files in os.walk(os.path.expanduser(mapdir), followlinks=True):
        for name in files:
            if name.endswith(fname):
                fullname = os.path.join(root, fname)
                break
            elif name.endswith(fname.replace('map','pmd')):
                fullname = os.path.join(root, fname.replace('map','pmd'))
                break
            elif name.endswith(fname.replace('L25','L3')):
                fullname = os.path.join(root, fname.replace('L25','L3'))
                break
            elif name.endswith(fname.replace('L25','L2').replace('JSMAP','PMAP')):
                fullname = os.path.join(root, fname.replace('L25','L2').replace('JSMAP','PMAP'))
                break
    # Get the data
    hdu = fits.open(fullname)
    img_data = hdu[1].data
    filter =  band
    if (band == 'B'):
        if (hdu[0].header['WAVELNTH'] == 100.0): 
           filter = 'green'
        else:
           filter = 'blue'
    elif (band == 'R'):
       filter = 'red'
    del hdu[1].header['CUNIT1'], hdu[1].header['CUNIT2']
    img_wcs = WCS(hdu[1].header)
    deg_per_pix = np.sqrt(np.abs(np.linalg.det(img_wcs.pixel_scale_matrix)))
    beams = {'blue':5.5, 'green':7.0, 'red':11.5, 'PSW':17.0, 'PMW':32.0, 'PLW':42.0}
    beam_size = beams[filter]/3600.
    mrkr_size = beam_size/deg_per_pix
    return(img_data, filter, mrkr_size, img_wcs)

def sourcelist_pscdb(obsid, filter, is_pacs=False):
    """ Return dataframe from source table

    Parameters:
    -----------
    obsid (int): observation id (10-digit integer)
    filter (string) : red, green, blue, PSW, PMW or PLW
    is_pacs (bool) : True if PACS, False if SPIRE

    Returns:
    --------
    sources : Pandas dataframe of the sources
    """
    import psycopg2 as pg
    import pandas.io.sql as psql
    if (is_pacs == False):
        with pg.connect("dbname=spire user=spire host=psc.ipac.caltech.edu") as connection:
            sources = psql.read_sql("""
                select sourceid, obsid, arrayname, x, y,
                ra, dec, flux, background, quality,
                ratml, dectml, fluxtml, backgroundparm1tml,
                ratm2, dectm2, fluxtm2, qualitydao
                from source
                where obsid={} and arrayname='{}'
                order by sourceid asc""".format(obsid, filter),
                connection)
        return(sources)
    else:
        with pg.connect("dbname=pacs user=gaborm host=localhost port=5562") as connection:
            sources = psql.read_sql("""
                select sourceid, obsid, band, susra,susdec,daora,daodec,susflux
                from source13
                where obsid={} and band='{}'
                order by sourceid asc""".format(obsid, filter),
                connection)
        return(sources)

def display_sources(sources, img_data, mrkr_size, wcs, cmap='grays',
        susscolor="blue", tmlcolor="green", tm2color="orange",
        titlestring="SPIRE PSC"):
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
    pos =  np.empty( shape=(0, 0) )
    if (nsrc > 0):
        if (is_pacs == True):
            sworld = np.vstack([sources['susra'].values.astype(np.float64),
                                sources['susdec'].values.astype(np.float64)]).T
        else:
            sworld = np.vstack([sources['ra'].values,sources['dec'].values]).T
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
    if ((nsrc > 0) and (susscolor != None)):
        p1 = scene.visuals.Markers(parent=view.scene)
        p1.set_data(pos,
             face_color=None, edge_color=susscolor, scaling=True,
             edge_width=2.0, size=mrkr_size)
    if ((nsrc > 0) and (tmlcolor != None)):
        tmlworld = np.vstack([sources['ratml'].values,sources['dectml'].values]).T
        postml = wcs.wcs_world2pix(tmlworld,0) + 0.5
        p2 = scene.visuals.Markers(parent=view.scene)
        p2.set_data(postml,
             face_color=None, edge_color=tmlcolor, scaling=True,
             edge_width=1.5, size=mrkr_size)
    if ((nsrc > 0) and (tm2color != None)):
        tm2world = np.vstack([sources['ratm2'].values,sources['dectm2'].values]).T
        postm2 = wcs.wcs_world2pix(tm2world,0) + 0.5
        p3 = scene.visuals.Markers(parent=view.scene)
        p3.set_data(postm2,
             face_color=None, edge_color=tm2color, scaling=True,
             edge_width=1.5, size=mrkr_size)
    app.run()
    return


if __name__ == '__main__' and sys.flags.interactive == 0:
    if (sys.argv[0].endswith('ppscinspector')):
        is_pacs = True
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("obsid", help="observation id", type=int)
    if (is_pacs):
        parser.add_argument("band", help="PACS band, must be B or R")
    else:
        parser.add_argument("band", help="SPIRE band, must be PSW, PMW or PMW")
    parser.add_argument("mapdir", help="top-level map directory")
    args = parser.parse_args()
    obsid = args.obsid
    band = args.band
    mapdir = args.mapdir
    if (is_pacs):
        img_data, filter, mrkr_size, wcs = find_map(obsid, band, mapdir, 
                 template="{}_PACS_L25_HPPJSMAP{}_SPGv13.0.0.fits.gz")
    else:
        img_data, filter, mrkr_size, wcs = find_map(obsid, band, mapdir)
    print('loading sources from database for {} {}...'.format(obsid,band), end='')
    sources = sourcelist_pscdb(obsid, filter, is_pacs=is_pacs)
    print('done.')
    if (is_pacs == True):
        titlestring = "PPSC: {} {}".format(obsid, filter)
        display_sources(sources, img_data, mrkr_size, wcs, titlestring=titlestring,
            tmlcolor=None, tm2color=None)
    else:
        titlestring = "SPSC: {} {}".format(obsid, filter)
        display_sources(sources, img_data, mrkr_size, wcs, titlestring=titlestring)
    
