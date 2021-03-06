"""provides caching for functions that operate on xarray.DataArrays or xarray.Datasets"""
import collections
import functools
import hashlib
import inspect
import json
import secrets
from pathlib import Path

import xarray as xr

hash_func = hashlib.sha1
_json = json

keys = (
    "hash",
    "hash_input",
    "hash_function",
    "cache",
    "function_name",
    "function_signature",
    "name",
    "xrcache_signature",
    "dataset",
    "array_name",
)
keys = collections.namedtuple("keys", keys)(*keys)

_cache = True  # use caching?
_path_cache = Path(keys.cache)  # default path for the cache
_implemented_types = (xr.DataArray, xr.Dataset)
_filename_hash_digits = 3


def path_cache():
    return _path_cache


def path_log():
    return _path_cache / f"{keys.hash}.json"


def get_hash(x, json=False):
    """hash x and digest"""
    if json:
        x = _json.dumps(x).encode()

    return hash_func(x).hexdigest()


def cached(*args, verbose=False):
    """On-disk cache for a function that operates on xarray.DataArray or Dataset"""

    def cached_decorator(func):
        @functools.wraps(func)
        def _func(array, cache=_cache, hash=None, **kwargs):
            if not cache:
                print(f"** Caching is deactivated, call function verbatim.")
                return func(array, **kwargs)

            assert any(isinstance(array, t) for t in _implemented_types)

            cache_signature = get_cache_signature(array, func, kwargs, hash=hash)
            hash = cache_signature[keys.hash]

            filename = cache_filename(array, func, hash=hash)

            # look up if the result is already stored in the local cache folder
            hash_lookup = log_lookup(filename)

            if hash_lookup == cache_signature[keys.hash]:
                return cache_read(filename, verbose=verbose)  # return the cached result

            # otherwise compute and attach metainfo
            result = func(array, **kwargs)
            result.attrs.update(cache_signature)

            cache_write(result, filename, verbose=verbose)

            return result

        return _func

    if len(args) == 1 and callable(args[0]):
        return cached_decorator(args[0])
    else:
        return cached_decorator


stored = cached


def get_cache_signature(array, func, kwargs, hash=None):
    """Collect signature of input data and function call for caching the result array"""
    hash_input = hash or hash_attrs(array.attrs)  # input data hash

    signature = get_signature_dict(func, array, kwargs)  # function call signature
    signature.update({keys.hash_input: hash_input})  # metainfo generated by xrcache

    hash_output = get_hash(signature, json=True)  # hash output array

    return {keys.hash: hash_output, keys.xrcache_signature: json.dumps(signature)}


def get_signature_dict(func, array, kwargs):
    """Create a signature dict for the function. Return default value for args as `None`
    """
    s = inspect.signature(func)
    dct = {"__name__": func.__name__}
    for (k, v) in s.parameters.items():
        if v.default == v.empty:
            dct.update({k: None})
        else:
            dct.update({k: v.default})
    dct.update(kwargs)  # update the signature
    dct.update({"__type__": str(type(array))})  # add data type
    dct.pop("kwargs", None)  # pop literal "kwargs" (if they were empty)

    signature = {keys.array_name: get_array_name(array), keys.function_signature: dct}

    return signature


def hash_attrs(attrs):
    """get hash from attrs or return random hash"""
    if keys.hash in attrs:
        hash_input = attrs.get(keys.hash)  # hash input array
    else:
        hash_input = secrets.token_hex()
        print(f"** no input hash found, create random hash:")
        print(hash_input)

    return hash_input


def log_update(filename, hash_str, verbose=False):
    """Update the hash logfile with current `filename: hash` pair"""
    path = path_log()
    log = {}
    if path.exists():
        log = json.load(path.open())
    log.update({filename: hash_str})

    if verbose:
        print(f"Update {path}")

    with path.open("w") as f:
        json.dump(log, f, indent=2)


def log_lookup(filename):
    """lookup hash for given filename"""
    path = path_log()
    if path.exists():
        log = json.load(path.open())
        return log.get(filename)


def function_name_from_attrs(attrs):
    """helper: extract function name from attrs"""
    s = json.loads(attrs[keys.function_signature])
    return s["__name__"]


def get_array_name(array):
    """return name of array or dataset"""
    if hasattr(array, "name"):
        name = array.name
    else:
        name = array.attrs.get(keys.name, keys.dataset)
    return name or ""


def cache_filename(array, function, hash=None):
    """determine filename for cache-file from the function name"""
    if any(isinstance(array, t) for t in _implemented_types):
        if hash is None:
            hash = hash_attrs(array.attrs)
        pre_name = f"{get_array_name(array)}__{function.__name__}"
        pre_name += f"__{hash[:_filename_hash_digits]}"
        name = f"{pre_name}.nc".strip("_")
        return name
    else:
        raise NotImplementedError(f"{type(array)} not (yet) implemented.")


def cache_write(array, filename, verbose=False):
    """write array to the cache"""
    h = array.attrs[keys.hash]  # extract hash
    file = _path_cache / filename
    file.parent.mkdir(exist_ok=True)  # make sure folder exists
    if verbose:
        print(f"Store array to {file}")
    array.to_netcdf(file)
    # update hash.json
    log_update(filename, h, verbose=verbose)


def cache_read(filename, verbose=False):
    """read file in cache folder"""
    path = _path_cache / filename
    try:
        result = xr.load_dataarray(path)
    except ValueError:
        result = xr.load_dataset(path)
    if verbose:
        print(f"Return stored {result.__class__.__name__} from {path}")

    return result
