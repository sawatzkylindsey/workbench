#!/usr/bin/python
# -*- coding: utf-8 -*-

import math


def scale(ranks):
    if len(ranks) == 0:
        return {}

    total = 0.0

    for k, v in ranks.items():
        assert v >= 0.0 and v <= 1.0
        total += v

    if total == 0.0:
        uniform = 1.0 / len(ranks)
        return {k: uniform for k, v in ranks.items()}
    else:
        return {k: v / total for k, v in ranks.items()}


def invert(ranks):
    if len(ranks) == 0:
        return {}

    ceiling = max(ranks.values()) * 2
    inverse_ranks = {}
    rolling_sum = 0.0

    for identifier, rank in ranks.items():
        assert rank >= 0.0 and rank <= 1.0, rank
        inverse_rank = ceiling - rank
        inverse_ranks[identifier] = inverse_rank
        rolling_sum += inverse_rank

    inverse_ranks = {identifier: rank / rolling_sum for identifier, rank in inverse_ranks.items()}
    assert math.isclose(1.0, sum(inverse_ranks.values()), abs_tol=0.005), sum(inverse_ranks.value())
    return inverse_ranks


def fit(ranks, target):
    assert len(ranks) > 0
    maximum = max(ranks.values())
    scaler = target / maximum
    return {k: v * scaler for k, v in ranks.items()}

