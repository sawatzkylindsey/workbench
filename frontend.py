#!/usr/bin/python
# -*- coding: utf-8 -*-


class d3node:
    def __init__(self, name, radius=1.0, alpha=1.0, coeff=0.5):
        self.name = name
        self.radius = radius
        self.alpha = alpha
        self.coeff = coeff


class d3link:
    def __init__(self, source, target, alpha=1.0):
        self.source = source
        self.target = target
        self.alpha = alpha

