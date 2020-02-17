import xarray as xr

import xrcache as xc

dataset_name = "dataset"
dataarray_name = "bar"

# create DataArray and Dataset
ds = xr.Dataset({dataarray_name: ("x", [1, 2, 3, 4]), "x": list("abcd")})
ds.attrs.update({xc.keys.name: dataset_name})
ds.attrs.update({xc.keys.hash: xc.get_hash(ds.bar.data)})

da = ds.bar
da.attrs.update({xc.keys.hash: xc.get_hash(da.data)})


@xc.cached
def some_dataset_function(dataset: xr.Dataset) -> xr.Dataset:
    """add square of input"""
    ds = dataset.copy()
    result = dataset.bar ** 2
    new_ds = ds.update({"foo": result})

    return new_ds


@xc.cached(verbose=True)
def some_dataarray_function(array: xr.DataArray) -> xr.DataArray:
    """add square of input"""
    return array ** 2


def test_cache_dataset(tmp_path):
    """run test in tmp folder"""
    xc._path_cache = tmp_path

    a = some_dataset_function(ds)
    filename = xc.cache_filename(a, some_dataset_function)

    assert (xc.path_cache() / filename).exists()
    assert xc.path_log().exists()

    b = some_dataset_function(ds)

    assert a.equals(b)
    assert a.attrs == b.attrs


def test_cache_dataarray(tmp_path):
    xc._path_cache = tmp_path

    a = some_dataarray_function(da)
    filename = xc.cache_filename(a, some_dataarray_function)

    assert (xc.path_cache() / filename).exists()
    assert xc.path_log().exists()

    b = some_dataarray_function(da)

    assert a.equals(b)
    assert a.attrs == b.attrs
