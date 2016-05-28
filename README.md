# Encode and organise your music collection

Transcodes Flac to Ogg and stores to any given directory in a hierarchical structure.

```
root/
|-- artist/
    |-- album/
        |-- 1 - Foo.ogg
        |-- 2 - Bar.ogg
```

## Setup instructions

I have only run this in a Linux environment under Python 3.5.1.

This requires [Taglib](http://taglib.github.io/), [Oggenc2](http://www.rarewares.org/ogg-oggenc.php) and [Flac](https://xiph.org/flac/).

In Debian/Ubuntu, this requires a simple

```bash
apt-get install flac libtag1-dev vorbis-tools
```

Afterwards, install this package with

```python
python setup.py install
```

which will install untz and the [Pytaglib](https://github.com/supermihi/pytaglib) dependency.

## Usage

```bash
untz --help
```
