# spscviz

This module has been developed for fast viewing of candidates from the
SPIRE and PACS Point Source Catalogs. Its intended audience is the
people working to make the catalogs -- in practical terms this applies
only to access to the working database.

Astropy, vispy, psycopg2, numpy and pandas are required. 

## Installation instructions

All the dependencies
except vispy and psycopg2 are available in a scientific Python distribution
such as [Anaconda](https://www.continuum.io/downloads). 

1. Install Anaconda from https://www.continuum.io/downloads#_macosx
It is recommended to install the Python 3.5 version. However, spscviz should 
work with the Python 2.7 version.

2. After installing Anaconda, check that `which python` and `which pip` point to your 
Anaconda installation.

3. Install psycopg2  
`conda install psycopg2`

3. Install the development version of VisPy:
First, check that `pip` is in your path from Anaconda by checking the output of `which pip`.
Then, install with  
`pip install https://github.com/vispy/vispy/archive/master.zip`

4. From https://github.com/stargaser/spscviz download the `spscinspector.py` file. 
Then make it executable with `chmod +x spscinspector.py`. 
Then you should be able to run `spscinspector.py` as a script, if the python in 
your path is the Anaconda one. 

## Running as a script

### SPIRE

For SPIRE, the module `spscinspector.py` can be run as a standalone script with arguments
of observation id, arrayname (PSW, PMW or PLW), and 
the top-level path of a directory containing maps of the form 
`{obsid}{band}_map.fits.zip`or `{obsid}{arrayname}_pmd.fits.zip`. It will query the database for the 
specified obsid and arrayname; find the corresponding map; and bring up a 
display window of the image with sources overlaid.

Circles are overlaid (by default) for the Sussextractor position (blue),
the timeline-fitter first run position (green), and the timeline-fitter
second run (orange).

### PACS

For PACS, run `ppscinspector`  as a standalone script with arguments
of observation id, band indicator (B or R), and 
the top-level path of a directory containing maps of the form 
`{obsid}_PACS_L25_HPPJSMAP{band}_SPGv13.0.0.fits.gz`or 
`{obsid}_PACS_L25_HPPPMAP{band}_SPGv13.0.0.fits.gz`. It will query the database for the 
specified obsid and arrayname; find the corresponding map; and bring up a 
display window of the image with sources overlaid.

## Data dependencies

The database query assumes that the user has set up their credentials 
in a ~/.pgpass file or equivalent. For PACS, it assumes an SSH tunnel to the
database has been set up on your local machine's port 5562.

The map directory assumes that you have a local copy of the Level 2+ maps.

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
titlestring = "SPSC: {} {}".format(myobsid, myarray)
display_sources(sources, img_data, mrkr_size, wcs, titlestring=titlestring)
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

For SPIRE, the source list must be a Pandas dataframe including these columns:

* `sourceid`
* `ra` and `dec`
* `fluxtml`
* `ratml` and `dectml`, if `tmlcolor` is not None
* `ratm2` and `dectm2`, if `tm2color` is not None

For PACS, the source list must include:

* `sourceid`
* `susra`, `susdec`, `susflux`

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
