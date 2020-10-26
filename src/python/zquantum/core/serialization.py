"""Serialization module."""
import json
from operator import attrgetter
from typing import Any, Iterator
import numpy as np
from .history.recorder import HistoryEntry, HistoryEntryWithArtifacts
from .bitstring_distribution import BitstringDistribution
from .utils import convert_array_to_dict, ValueEstimate, SCHEMA_VERSION


def preprocess(tree):
    """This inflates namedtuples into dictionaries, otherwise they would be serialized as lists.

    KJ: I found initial version of this code a while ago in a related SO question:
    https://stackoverflow.com/questions/43913256/understanding-subclassing-of-jsonencoder
    """
    if isinstance(tree, dict):
        return {k: preprocess(v) for k, v in tree.items()}
    elif isinstance(tree, tuple) and hasattr(tree, "_asdict"):
        return preprocess(tree._asdict())
    elif isinstance(tree, ValueEstimate):
        return tree.to_dict()
    elif isinstance(tree, (list, tuple)):
        return list(map(preprocess, tree))
    return tree


class ZapataEncoder(json.JSONEncoder):
    ENCODERS_TABLE = {
        np.ndarray: convert_array_to_dict,
        ValueEstimate: ValueEstimate.to_dict,
        BitstringDistribution: attrgetter("distribution_dict"),
    }

    def default(self, o: Any):
        if type(o) in self.ENCODERS_TABLE:
            return self.ENCODERS_TABLE[type(o)](o)
        return o

    def encode(self, o: Any):
        return super().encode(preprocess(o))

    def iterencode(self, o: Any, _one_shot: bool = ...) -> Iterator[str]:
        return super().iterencode(preprocess(o))


class ZapataDecoder(json.JSONDecoder):
    """Custom decoder for loading data dumped by ZapataEncoder."""

    SCHEMA_MAP = {
        "zapata-v1-value_estimate": ValueEstimate.from_dict
    }

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs
        )

    def object_hook(self, obj):
        # Parts of the below if-elif-else are sketchy, because for some objects there is
        # no defined schema and we are matching object's type based on deserialized
        # dict's contents.
        if "real" in obj:
            array = np.array(obj["real"])
            if "imag" in obj:
                array = array + 1j * np.array(obj["imag"])
            return array
        elif "call_number" in obj and "value" in obj:
            cls = HistoryEntry if "artifacts" not in obj else HistoryEntryWithArtifacts
            return cls(**obj)
        elif "schema" in obj and obj["schema"] in self.SCHEMA_MAP:
            return self.SCHEMA_MAP[obj.pop("schema")](obj)
        else:
            return obj


def save_optimization_results(optimization_results, filename):
    optimization_results["schema"] = SCHEMA_VERSION + "-optimization_result"
    with open(filename, "wt") as target_file:
        json.dump(optimization_results, target_file, cls=ZapataEncoder)
