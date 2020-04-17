# -*- coding: utf-8 -*-

""""Single Layer Constraints module APIs

.. note:: This program is free software; you can redistribute it and/or modify
    it under the terms of the Mozilla Public License 2.0.

"""

__author__ = 'elpaso@itopen.it'
__date__ = '2020-04-16'
__copyright__ = 'Copyright 2020, Gis3w'

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from core.api.authentication import CsrfExemptSessionAuthentication

from qdjango.models.constraints import Constraint, ConstraintRule
from qdjango.api.constraints.serializers import SingleLayerConstraintSerializer, SingleLayerConstraintRuleSerializer
from qdjango.api.constraints.permissions import SingleLayerConstraintPermission, SingleLayerConstraintRulePermission
from qdjango.models import Layer
import json


class SingleLayerConstraintList(generics.ListCreateAPIView):
    """List of constraints, optionally filtered by editing layer id"""

    queryset = Constraint.objects.all()
    serializer_class = SingleLayerConstraintSerializer

    permission_classes = (
        SingleLayerConstraintPermission,
    )

    authentication_classes = (
        CsrfExemptSessionAuthentication,
    )

    def get_queryset(self):
        """
        This view should return a list constraints for a given layer QGIS id (qgs_layer_id) portion of the URL.
        """

        qs = super().get_queryset()
        if 'layer_id' in self.kwargs:
            qs = qs.filter(layer_id =self.kwargs['layer_id'])
        if 'qgs_layer_id' in self.kwargs:
            qs = qs.filter(layer__qgs_layer_id=self.kwargs['qgs_layer_id'])
        return qs

    def create(self, request, *args, **kwargs):
        """Handle IntegrityError and raise 400"""

        with transaction.atomic():
            try:
                return super(SingleLayerConstraintList, self).create(request, *args, **kwargs)
            except IntegrityError as ex:
                content = {'error': 'IntegrityError %s' % ex.message.decode('utf8') }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)


class SingleLayerConstraintDetail(generics.RetrieveUpdateDestroyAPIView):
    """Details of a constraint"""

    queryset = Constraint.objects.all()
    serializer_class = SingleLayerConstraintSerializer

    permission_classes = (
        SingleLayerConstraintPermission,
    )

    authentication_classes = (
        CsrfExemptSessionAuthentication,
    )


class SingleLayerConstraintRuleList(generics.ListCreateAPIView):
    """List of constraint rules, optionally filtered by editing layer QGIS id, user id or constraint id"""

    queryset = ConstraintRule.objects.all()
    serializer_class = SingleLayerConstraintRuleSerializer

    permission_classes = (
        SingleLayerConstraintRulePermission,
    )

    authentication_classes = (
        CsrfExemptSessionAuthentication,
    )

    def get_queryset(self):
        """
        This view should return a list constraints for a given layer id (qgs_layer_id) or user_id or constraint_id portions of the URL.

        Note that if user_id is specified a match for user groups will be also attempted.

        """

        qs = super().get_queryset()
        if 'layer_id' in self.kwargs:
            qs = qs.filter(constraint__layer_id=self.kwargs['layer_id'])
        if 'qgs_layer_id' in self.kwargs:
            qs = qs.filter(constraint__layer__qgs_layer_id=self.kwargs['qgs_layer_id'])
        if 'user_id' in self.kwargs:
            user = User.objects.get(pk=self.kwargs['user_id'])
            user_groups = user.groups.all()
            if user_groups.count():
                qs = qs.filter(Q(user=user)|Q(group__in=user_groups))
            else:
                qs = qs.filter(user=user)
        if 'constraint_id' in self.kwargs:
            qs = qs.filter(constraint_id=self.kwargs['constraint_id'])
        return qs


    def create(self, request, *args, **kwargs):
        """Handle IntegrityError and raise 400"""

        with transaction.atomic():
            try:
                return super().create(request, *args, **kwargs)
            except IntegrityError as ex:
                content = {'error': 'IntegrityError %s' % ex.message.decode('utf8') }
                return Response(content, status=status.HTTP_400_BAD_REQUEST)


class SingleLayerConstraintRuleDetail(generics.RetrieveUpdateDestroyAPIView):
    """Details of a constraint rule"""

    authentication_classes = (
        CsrfExemptSessionAuthentication,
    )

    permission_classes = (
        SingleLayerConstraintRulePermission,
    )

    queryset = ConstraintRule.objects.all()
    serializer_class = SingleLayerConstraintRuleSerializer

