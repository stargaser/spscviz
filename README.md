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
`{obsid}{band}_map.fits.zip`or `{obsid}{arrayname}_pmd.fits.zip`. It will find the
corresponding map; query the database for the 
specified obsid and band; and bring up a 
display window of the image with sources overlaid.

Circles are overlaid (by default) for the Sussextractor position (blue),
the timeline-fitter first run position (green), and the timeline-fitter
second run (orange).

### PACS

For PACS, run `ppscinspector`  as a standalone script with arguments
of observation id, band indicator (B or R), and 
the top-level path of a directory containing maps of the form 
`{obsid}_PACS_L25_HPPJSMAP{band}_SPGv13.0.0.fits.gz`or 
`{obsid}_PACS_L25_HPPPMAP{band}_SPGv13.0.0.fits.gz`. It will find the corresponding map
and infer the filter; query the database for the 
specified obsid and filter;  and bring up a 
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
* T or t: move the high and low stretch values up
* B or b: move the high and low stretch values down
* W or w: widen the difference between high and low stretch values (decrease contrast)
* N or n: narrow the difference between high and low stretch values (increase contrast)
* U or u: in the terminal, user input of low and high stretch values
* L or l: print in your terminal all the information for the current source that was 
queried from the database.
* M or m: Start movie mode (center on sources automatically)
* S or s: Stop movie mode
* F11: make the display window full-screen
* Esc: close the display window

## Optional arguments

Type `spscinspector.py -h` to see the SPIRE defaults:

```
usage: spscinspector.py [-h] [--cmap [CMAP]] [-S [SQL_STATEMENT]]
                        [-D [DBNAME]] [-U [USERNAME]] [-H [HOSTNAME]]
                        [-P [PORT]]
                        obsid band mapdir

positional arguments:
  obsid                 observation id
  band                  SPIRE band, must be PSW, PMW or PMW
  mapdir                top-level map directory

optional arguments:
  -h, --help            show this help message and exit
  --cmap [CMAP]         color map, (grays|fire|ice|hot|spring|summer| autumn|w
                        inter|blues|cool|hsl|husl|diverging|cubehelixcolormap)
  -S [SQL_STATEMENT], --sql_statement [SQL_STATEMENT]
                        SQL statement, default=" select sourceid, obsid,
                        arrayname, x, y, ra, dec, flux, background, quality,
                        ratml, dectml, fluxtml, backgroundparm1tml, ratm2,
                        dectm2, fluxtm2, qualitydao from source where obsid={}
                        and arrayname='{}' order by sourceid asc "
  -D [DBNAME], --dbname [DBNAME]
                        database name, default=spire
  -U [USERNAME], --username [USERNAME]
                        database username, default=spire
  -H [HOSTNAME], --hostname [HOSTNAME]
                        database hostname, default=psc.ipac.caltech.edu
  -P [PORT], --port [PORT]
                        database port, default 5432
```

Type `ppscinspector -h` to see the PACS defaults:

```
usage: ppscinspector [-h] [--cmap [CMAP]] [-S [SQL_STATEMENT]] [-D [DBNAME]]
                     [-U [USERNAME]] [-H [HOSTNAME]] [-P [PORT]]
                     obsid band mapdir

positional arguments:
  obsid                 observation id
  band                  PACS band, must be B or R
  mapdir                top-level map directory

optional arguments:
  -h, --help            show this help message and exit
  --cmap [CMAP]         color map, (grays|fire|ice|hot|spring|summer| autumn|w
                        inter|blues|cool|hsl|husl|diverging|cubehelixcolormap)
  -S [SQL_STATEMENT], --sql_statement [SQL_STATEMENT]
                        SQL statement, default=" select sourceid, obsid, band,
                        susra,susdec,daora,daodec,susflux from source13 where
                        obsid={} and band='{}' order by sourceid asc "
  -D [DBNAME], --dbname [DBNAME]
                        database name, default=pacs
  -U [USERNAME], --username [USERNAME]
                        database username, default=gaborm
  -H [HOSTNAME], --hostname [HOSTNAME]
                        database hostname, default=localhost
  -P [PORT], --port [PORT]
                        database port, default 5562
```

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
sql_statement = """
        select sourceid, obsid, arrayname, x, y,
        ra, dec, flux, background, quality,
        ratml, dectml, fluxtml, backgroundparm1tml,
        ratm2, dectm2, fluxtm2, qualitydao
        from source
        where obsid={} and arrayname='{}'
        order by sourceid asc
"""
dbname="spire"
username="spire"
hostname="psc.ipac.caltech.edu"
port=5432
img_data, filter, mrkr_size, img_wcs = \
     spscinspector.find_map(myobsid,myarray,'~/data/spsc/level2/20151007')
sources = spscinspector.sourcelist_pscdb(myobsid, filter, sql_statement,
       dbname, username, hostname, port)
titlestring = "SPSC: {} {}".format(myobsid, filter)
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

You can change the SQL statement either on the command line, or in an interactive
session as shown above.

### Contributors

David Shupe, IPAC (most of the code)
Gábor Marton, Konkoly (modifications for PACS, and testing)
Bernhard Schulz, IPAC (coding suggestions and testing)