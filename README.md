# spscviz

This module is intended for fast viewing of candidates from the SPIRE Point Source Catalog. It is intended
for people working to make the catalog.

Astropy, vispy, numpy and pandas are required. A development version of vispy (0.5.0 track) needed and can be installed with
`pip install https://github.com/vispy/vispy/archive/master.zip`.

The module `spscinspector.py` can be run by itself with argument of observation id, arrayname (PSW, PMW or PLW), and 
the top-level path of a directory containing maps of the form obsidarrayname_map.fits.zip. It will query the database for the 
specified obsid and arrayname; find the corresponding map; and bring up a display window of the image with sources overlaid.

Clicking in the display window allows up-arrow, down-arrow, left-arrow and right-arrow to be used to quickly pan on the sources. 
The image display is adjusted based on the pixel values in the currently-zoomed portion of the image.
A movie mode can be started with "m" and stopped with "s". Spacebar also increments through the images.

The database query assumes that the user has set up their credentials in a ~/.pgpass file or equivalent.

The individual functions in `spscinspector.py` can be called on their own in an interactive Python session.
