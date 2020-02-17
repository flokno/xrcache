WIP: xrcache | on-disk cache for numerical functions working with xarray
===

![python](https://img.shields.io/badge/python-3.5--3.8-lightgrey.svg?style=flat)
[![pypi](https://img.shields.io/pypi/v/xrcache.svg?style=flat)](https://pypi.org/project/xrcache/)
![license](https://img.shields.io/pypi/l/xrcache.svg?color=red&style=flat)
[![code style](https://img.shields.io/badge/code%20style-black-202020.svg?style=flat)](https://github.com/ambv/black)

## Disclaimer

This is work in progress, things change fast.

## What is this?

_xrcache_ provides on-disk caching for functions operating on `xarray.DataArray` or `xarray.Dataset`, see [xarray documentation](http://xarray.pydata.org/).

## How does it work?

_xrcache_ provides a decorator that turns a function into a cached function, which means it saves its result to the `cache` folder as `xarray.DataArray` or `xarray.Dataset` and _automatically_ re-uses this result if it receives the same input again.

### Hash Philosophy

Each `Dataset` is assigned a `hash` for identification. The initial hash for the data has to be provided by the user (see example below). All subsequent hashes are generated deterministically from the `hash_input`, i.e., the `hash` of the input data, and `hash_function`, a hash generated from the signature of the function that is called.

## Who needs this?

People who like to work with `xarray.DataArray` and `xarray.Dataset` and like to store intermediate results of their workflows locally, and speedup recalculation of intermediate steps.

## Example

```python
import xarray as xr
import xrcache as xc

# create a generic named dataset and assign a hash to its `attrs`
ds = xr.Dataset({"bar": ("x", [1, 2, 3, 4]), "x": list("abcd")})
ds.attrs.update({"name": "dataset"})  # <- name your data!
ds.attrs.update({xc.keys.hash: "some_hash"})  # <- important


# define some function that works on the dataset, e.g.
def function(dataset: xr.Dataset) -> xr.Dataset:
    """add square of input"""
    ds = dataset.copy()
    result = dataset.bar ** 2
    new_ds = ds.update({"foo": result})

    return new_ds


# make it a cached function with xrcache
@xc.cached
def cached_function(dataset):
    return function(dataset)
```

Check out the notebooks in `/doc`.

## Changelog

v0.0.4: Allow `func(..., cache=False, hash='some_other_hash')` for more fine grained control. Add 3 digits of the hash to the cache file to avoid clashes.

v0.0.3: Add array/dataset names to stored files, introduce `@stored`, simplify attached data, allow `@cached(verbose=True)`

v0.0.2: include project description on pypi

v0.0.1: initial commit
