# spscviz

This module has been developed for fast viewing of candidates from the SPIRE Point 
Source Catalog. Its intended audience is the people working to make the catalog --
in practical terms this applies only to access to the working database.

Astropy, vispy, numpy and pandas are required. All the dependencies
except vispy are available in a scientific Python distribution
such as [Anaconda](https://www.continuum.io/downloads). 
A development version of 
[vispy](http://vispy.org) (0.5.0 track) is needed and can be installed with
`pip install https://github.com/vispy/vispy/archive/master.zip`.

## Running as a script

The module `spscinspector.py` can be run as a standalone script with arguments
of observation id, arrayname (PSW, PMW or PLW), and 
the top-level path of a directory containing maps of the form 
`obsidarrayname_map.fits.zip`or `obsidarrayname_pmd.fits.zip`. It will query the database for the 
specified obsid and arrayname; find the corresponding map; and bring up a 
display window of the image with sources overlaid.

Circles are overlaid (by default) for the Sussextractor position (blue),
the timeline-fitter first run position (green), and the timeline-fitter
second run (orange).

## Data dependencies

The database query assumes that the user has set up their credentials 
in a ~/.pgpass file or equivalent.

The map directory assumes that you have a local copy of the Level 2 maps.

## Controlling the display 

Click in the display window to allow interaction. Resize the window
to your liking and zoom in with a mouse wheel or touchpad gesture.
The image stretch is based at the low end on the pixel values in the
currently-zoomed view (the currently-visible pixels). At the high end
the stretch is based on the timeline-fitter flux.

The display is intended to allow rapid inspection of the source list.
Here are the key mappings:

* Left-arrow, down-arrow, or spacebar: go to the next source in the list.
* Right-arrow or up-arrow: go backward one source.
* L or l: print in your terminal all the information for the current source that was 
queried from the database.
* M or m: Start movie mode (center on sources automatically)
* S or s: Stop movie mode
* F11: make the display window full-screen
* Esc: close the display window

## Running in an interactive session

The individual functions in `spscinspector.py` can be called on 
their own in an interactive Python session. This may be preferable 
for starting with a source list spanning many observations, as the
database query takes several seconds to load sources.

Additionally, it is possible to pick a different colormap, different colors
for the markers, or turning off certain markers, by calling the functions
interactively.  It is also possible to run several instances of the display
simultaneously.

An example calling sequence inside an interactive session with defaults is:

```
import spscinspector
myobsid = 1342231851
myarray = 'PSW'
sources = spscinspector.sourcelist_pscdb(myobsid, myarray)
img_data, mrkr_size, img_wcs = \
     spscinspector.find_map(myobsid,myarray,'~/data/spsc/level2/20151007')
spscinspector.display_sources(sources, img_data, mrkr_size, img_wcs)
```

### Tailoring colors or removing markers

To try a different color scheme, (and to turn off the markers for the
first run of timeline fitter), change the display line:
```
spscinspector.display_sources(sources, img_data, mrkr_size, img_wcs,
   cmap='fire', susscolor='black',tmlcolor=None,tm2color='yellow')
```

To get a list of available colormap names:
```
import vispy
vispy.color.get_colormaps()
```

### Tailoring the source list

The source list must be a Pandas dataframe including these columns:

* `sourceid`
* `ra` and `dec`
* `fluxtml`
* `ratml` and `dectml`, if `tmlcolor` is not None
* `ratm2` and `dectm2`, if `tm2color` is not None

The default query in `spscinspector.sourcelist_pscdb` retrieves a number of other
parameters. In an interactive session, you may wish to use a different query to
the database, or to load the source list dataframe from some other data source.

To change the query, use the lines from the `sourcelist_pscdb` function and change
the SQL query as desired.
```
import psycopg2 as pg
import pandas.io.sql as psql
obsid = 1342231851
array = 'PSW'
with pg.connect("dbname=spire user=spire host=psc.ipac.caltech.edu") as connection:
    sources = psql.read_sql("""
        select sourceid, obsid, arrayname, x, y,
        ra, dec, flux, background, quality,
        ratml, dectml, fluxtml, backgroundparm1tml,
        ratm2, dectm2, fluxtm2, qualitydao
        from source
        where obsid={} and arrayname='{}'
        order by sourceid asc""".format(obsid, arrayname),
        connection)
```