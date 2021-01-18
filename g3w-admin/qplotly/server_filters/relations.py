# coding=utf-8
""""Server filters for relations.

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the Mozilla Public License 2.0.

"""

__author__ = 'lorenzetti@gis3w.it'
__date__ = '2021-01-15'
__copyright__ = 'Copyright 2015 - 2021, Gis3w'

from core.api.filters import BaseFilterBackend


class ByFatherFeatursFilter(BaseFilterBackend):
    """A filter backend that applies a QgsExpression to QplotlyFactory"""

    def apply_filter(self, request, qgis_layer, qgis_feature_request, view=None):
        """Apply the filter to the QGIS feature request or the layer's subset string
        Warning: if the filter alters the layer instance (for example by settings a subset
        string) make sure to restore the original state or to work on a clone.
        """

        expression_text = getattr(view, 'father_features_expresion', None)

        if not expression_text:
            return

        original_expression = qgis_feature_request.filterExpression(
        ) if qgis_feature_request is not None else None
        if original_expression is not None:
            qgis_feature_request.setFilterExpression("({original_expression}) AND ({extra_expression})"
                                                     .format(original_expression=original_expression.expression(),
                                                             extra_expression=expression_text))
        else:
            qgis_feature_request.setFilterExpression(expression_text)