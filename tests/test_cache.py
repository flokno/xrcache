import xarray as xr

import xrcache as xc

# create Dataset
ds = xr.Dataset({"bar": ("x", [1, 2, 3, 4]), "x": list("abcd")})

hash_str = xc.get_hash(ds.bar.data)

ds.attrs.update({xc.keys.hash: hash_str})


# define function that uses cache
@xc.cached
def some_dataset_function(dataset: xr.Dataset) -> xr.Dataset:
    """add square of input"""
    ds = dataset.copy()
    result = dataset.bar ** 2
    new_ds = ds.update({"foo": result})

    return new_ds


def test_cache_dataset(tmp_path):
    """run test in tmp folder"""
    xc._path_cache = tmp_path

    a = some_dataset_function(ds)

    assert (xc.path_cache() / "some_dataset_function.nc").exists()
    assert xc.path_log().exists()

    b = some_dataset_function(ds)

    assert a.equals(b)
    assert a.attrs == b.attrs
