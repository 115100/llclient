# Encode and organise your music collection

Transcodes Flac to Vorbis and stores to any given directory in a hierarchical structure.

```
root/
|-- artist/
    |-- album/
        |-- 1 - Foo.ogg
        |-- 2 - Bar.ogg
```

## Setup instructions

This requires
- [Taglib](http://taglib.github.io/)
- [loudgain/rgbpm](https://github.com/Moonbase59/loudgain)
- [Flac](https://xiph.org/flac/)

Opus encoding requires [opus-tools](https://opus-codec.org/downloads/).

Vorbis encoding requires [Oggenc2](http://www.rarewares.org/ogg-oggenc.php).

Cue handling requires [shntool](http://shnutils.freeshell.org/shntool/) and
[cuetools](https://github.com/svend/cuetools).

You may need additional codecs depending on what format your source audio is.

Afterwards, install this package with

```python
python setup.py install
```

which will install untz and the [Pytaglib](https://github.com/supermihi/pytaglib) dependency.

## Usage

```bash
untz --help
```
