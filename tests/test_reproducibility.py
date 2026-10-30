
import numpy as np


def generate_sample(seed):
    rng = np.random.default_rng(seed)

    flow = rng.normal(loc=100.0, scale=5.0, size=10)
    pressure = rng.normal(loc=300.0, scale=10.0, size=10)

    return flow, pressure


def test_same_seed_produces_same_values():
    flow1, pressure1 = generate_sample(20261022)
    flow2, pressure2 = generate_sample(20261022)

    assert np.array_equal(flow1, flow2)
    assert np.array_equal(pressure1, pressure2)


def test_different_seeds_produce_different_values():
    flow1, _ = generate_sample(20261022)
    flow2, _ = generate_sample(12345)

    assert not np.array_equal(flow1, flow2)
