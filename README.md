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

The module `spscinspector.py` can be run as a standalone script with arguments
of observation id, arrayname (PSW, PMW or PLW), and 
the top-level path of a directory containing maps of the form 
`obsidarrayname_map.fits.zip`. It will query the database for the 
specified obsid and arrayname; find the corresponding map; and bring up a 
display window of the image with sources overlaid.

Clicking in the display window allows up-arrow, down-arrow, left-arrow and right-arrow
to be used to quickly center on individual sources. Spacebar also 
increments through the sources.
The mouse wheel or equivalent can be used for zooming. 
The image display is adjusted based on the pixel values in the currently-zoomed
portion of the image.
Pressing letter "L" will print the current sourceid and x,y pixel location.
A movie mode can be started with "m" and stopped with "s". 
F11 will make the window full-screen and ESC will close it.

The database query assumes that the user has set up their credentials 
in a ~/.pgpass file or equivalent.

The individual functions in `spscinspector.py` can be called on 
their own in an interactive Python session. This may be preferable 
for starting with a source list spanning many observations, as the
database query takes several seconds to load sources.
