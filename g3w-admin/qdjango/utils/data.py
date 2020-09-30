# -*- coding: utf-8 -*-
import json
import os
import re
import logging
from collections import OrderedDict

from defusedxml import lxml
from django.conf import settings
from django.db import transaction
from django.http.request import QueryDict
from django.utils.translation import ugettext_lazy as _
from lxml import etree

from qgis.core import (
    QgsProject, QgsMapLayer,
    QgsUnitTypes,
    QgsProjectVersion,
    QgsWkbTypes,
    QgsEditFormConfig,
    QgsAttributeEditorElement,
    QgsRectangle
)

from qgis.gui import QgsMapCanvas

from qgis.server import QgsServerProjectUtils

from qgis.PyQt.QtCore import QVariant, Qt
from qgis.core import QgsMasterLayoutInterface, QgsLayoutItemMap, QgsLayout

from core.utils.data import XmlData, isXML
from core.utils.qgisapi import count_qgis_features
from qdjango.models import Project

from .exceptions import QgisProjectException
from .structure import *
from .validators import (CheckMaxExtent, ColumnName, DatasourceExists, ProjectExists,
                         IsGroupCompatibleValidator, ProjectTitleExists,
                         UniqueLayername)



# constant per qgis layers
QGIS_LAYER_TYPE_NO_GEOM = 'NoGeometry'



def makeDatasource(datasource, layerType):
    """
    Rebuild datasource on qgjango/g3w-admin settings
    :param datasource:
    :param layerType:
    :return: string, new datasource
    """
    newDatasource = None
    # Path and folder name
    basePath = settings.DATASOURCE_PATH.rstrip('/') # eg: /home/sit/charts
    folder = os.path.basename(basePath) # eg: charts
    # OGR example datasource:
    # Original: <datasource>\\SIT-SERVER\sit\charts\definitivo\d262120.shp</datasource>
    # Modified: <datasource>/home/sit/charts\definitivo\d262120.shp</datasource>
    if layerType == Layer.TYPES.ogr or layerType == Layer.TYPES.gdal:
        newDatasource = re.sub(r'(.*?)%s(.*)' % folder, r'%s\2' % basePath, datasource) # ``?`` means ungreedy


    if layerType == Layer.TYPES.delimitedtext:
        oldPath = re.sub(r"(.*)file:(.*?)", r"\2", datasource)
        newPath = re.sub(r'(.*?)%s(.*)' % folder, r'%s\2' % basePath, oldPath)
        newDatasource = datasource.replace(oldPath, newPath)

    # SpatiaLite example datasource:
    # Original: <datasource>dbname='//SIT-SERVER/sit/charts/Carte stradali\\naturalearth_110m_physical.sqlite' table="ne_110m_glaciated_areas" (geom) sql=</datasource>
    # Modified: <datasource>dbname='/home/sit/charts/Carte stradali\\naturalearth_110m_physical.sqlite' table="ne_110m_glaciated_areas" (geom) sql=</datasource>
    if layerType == Layer.TYPES.spatialite:
        oldPath = re.sub(r"(.*)dbname='(.*?)'(.*)", r"\2", datasource) # eg: "//SIT-SERVER/sit/charts/Carte stradali\\naturalearth_110m_physical.sqlite"
        newPath = re.sub(r'(.*?)%s(.*)' % folder, r'%s\2' % basePath, oldPath) # eg: "\home\sit\charts/Carte stradali\\naturalearth_110m_physical.sqlite" (``?`` means ungreedy)
        newDatasource = datasource.replace(oldPath, newPath)

    return newDatasource

def makeComposerPictureFile(file):
    """
    For ComposerPicture rebuild for DATASOURCE_PATH
    :param file:
    :return:
    """
    new_file = None
    # Path and folder name
    basePath = settings.DATASOURCE_PATH.rstrip('/')  # eg: /home/sit/charts
    folder = os.path.basename(basePath)  # eg: charts

    new_file = re.sub(r'(.*?)%s(.*)' % folder, r'%s\2' % basePath, file)  # ``?`` means ungreedy
    return new_file.split('|')[0]


class QgisProjectLayer(XmlData):
    """
    Qgisdata object for layer project: a layer xml wrapper
    """

    _dataToSet = [
        'layerId',
        'isVisible',
        'title',
        'name',
        'layerType',
        'minScale',
        'maxScale',
        'scaleBasedVisibility',
        'srid',
        'wfsCapabilities',
        'editOptions',
        'datasource',
        'origname',
        'aliases',
        'columns',
        'excludeAttributesWMS',
        'excludeAttributesWFS',
        'geometrytype',
        'vectorjoins',
        'editTypes',
        'editorlayout',
        'editorformstructure',
        'extent'
    ]

    _pre_exception_message = 'Layer'

    _defaultValidators = [
        DatasourceExists,
        #ColumnName
    ]

    _layer_model = Layer

    def __init__(self, layer, **kwargs):
        self.qgs_layer = layer

        if 'qgisProject' in kwargs:
            self.qgisProject = kwargs['qgisProject']

        # FIXME: check il order on layer is used
        self.order = kwargs['order'] if 'order' in kwargs else 0


        # set data value into this object
        self.setData()

        # register default validator
        self.validators = []
        for validator in self._defaultValidators:
            self.registerValidator(validator)


    def __str__(self):
        """
        StrId Object for error
        """
        return self._getDataLayerId()

    def _getDataName(self):
        """
        Get name(shortname)
        :return: name(shortname) layer property
        :rtype: str
        """

        name = self.qgs_layer.shortName()
        if not name:
            name = self.qgs_layer.name()
        return name

    def _getDataOrigname(self):
        """
        Get layer QGIS origname value
        :return: QGIS origin name by layer type
        :rtype: str
        """
        if self.layerType == Layer.TYPES.ogr:
            name = os.path.splitext(os.path.basename(self.datasource))[0]
        elif self.layerType == Layer.TYPES.gdal:
            if isXML(self.datasource):
                name = self.name
            else:
                if self.datasource.startswith('PG:'):

                    # add whitespace to datasource string for re findall
                    dts = datasource2dict(self.datasource + ' ')
                    name = re.sub('["\']', "", dts['table'].split('.')[-1])
                else:
                    name = os.path.splitext(os.path.basename(self.datasource))[0]
        elif self.layerType == Layer.TYPES.postgres or self.layerType == Layer.TYPES.spatialite:
            dts = datasource2dict(self.datasource)
            name = dts['table'].split('.')[-1].replace("\"", "")
        elif self.layerType ==Layer.TYPES.wms:
            dts = QueryDict(self.datasource)
            try:
                name = dts['layers']
            except KeyError:
                name = self.name
        else:
            name = self.qgs_layer.name()

        return name

    def _getDataLayerId(self):
        """
        Get name tag content from xml
        :return: return QGIS layerID
        :rtype: str
        """

        return self.qgs_layer.id()

    def _getDataTitle(self):
        """
        Get title tag content from xml
        :return: layer title
        :rtype: str
        """

        return self.qgs_layer.name()

    def _getDataIsVisible(self):
        """
        Get if is visible form lqyerRoot
        :return: layer visibility
        :rtype: bool
        """

        # TODO: check if is it possibile use isVisible from node of layer-tree-group.
        #  Check PyQGIS method to read project '<legend>' section.
        return self.qgisProject.qgs_project.layerTreeRoot().findLayer(self.qgs_layer).isVisible()

    def _getDataLayerType(self):
        """
        Get name tag content from xml
        :return: qgis layer type
        :rtype: str
        """
        availableTypes = [item[0] for item in Layer.TYPES]
        layer_type = self.qgs_layer.dataProvider().name()
        if not layer_type in availableTypes:
            raise Exception(_('Missing or invalid type for layer')+' "%s"' % layer_type)
        return layer_type

    def _getDataMinScale(self):
        """
        Get min_scale from layer attribute
        :return: layer min scale value
        :rtype: int
        """
        return int(self.qgs_layer.minimumScale())

    def _getDataMaxScale(self):
        """
        Get max_scale from layer attribute
        :return: max scale value for layer
        :rtype: int
        """
        return int(self.qgs_layer.maximumScale())

    def _getDataScaleBasedVisibility(self):
        """
        Get scale based visibility property from layer attribute
        :return: boolean visibility by scale
        :rtype: bool
        """
        return self.qgs_layer.hasScaleBasedVisibility()

    def _getDataSrid(self):
        """
        Get srid property of layer
        :return: ESPG srid code
        :rtype: int, None
        """
        return self.qgs_layer.crs().postgisSrid()

    def _getDataVectorjoins(self):
        """
        Get relations layer section into project
        :param layerTree:
        :return: list of dict fo vector joins structure or none is not set
        :rtype: list, None
        """

        # get root of layer-tree-group
        ret = []
        try:
            vectorjoins = self.qgs_layer.vectorJoins()
            for order, join in enumerate(vectorjoins):
                ret.append(
                    {
                        "cascadedDelete": str(int(join.hasCascadedDelete())),
                        "targetFieldName": join.targetFieldName(),
                        "editable": str(int(join.isEditable())),
                        "memoryCache": str(int(join.isUsingMemoryCache())),
                        "upsertOnEdit": str(int(join.hasUpsertOnEdit())),
                        "joinLayerId": join.joinLayerId(),
                        "dynamicForm": str(int(join.isDynamicFormEnabled())),
                        "joinFieldName": join.joinFieldName()

                    }
                )
        except:
            pass
        return ret

    def _getDataCapabilities(self):
        return 1


    def _getDataGeometrytype(self):
        """
        Get geometry from layer attribute
        :return: strting of geometry type
        :rtype: str, None
        """

        try:
            return QgsWkbTypes.displayString(self.qgs_layer.wkbType())
        except:
            return None

    def _getDataEditOptions(self):
        """
        Get bit value from WFSTLayers section
        :return: bitwise for WFST layer state
        :rtype: int
        """

        # TODO: ask to elpaso
        editOptions = 0
        for editOp, layerIds in list(self.qgisProject.wfstLayers.items()):
            if self.layerId in layerIds:
                editOptions |= getattr(settings, editOp)

        return None if editOptions == 0 else editOptions

    def _getDataWfsCapabilities(self):
        """
        Set wfs capability for layer.
        :return: bitwise WFS layer capabilities: 0 not queryable, 1 queryable.
        :rtype: int
        """

        # TODO: ask to elpaso
        wfsCapabilities = 0
        for wfslayer in self.qgisProject.wfsLayers:
            if self.layerId in wfslayer:
                wfsCapabilities = settings.QUERYABLE

        return None if wfsCapabilities == 0 else wfsCapabilities

    def _getDataDatasource(self):
        """
        Get datasource for layer.
        :return: QGIS project datasource string or new datasource string for OGR and GDAL and SpatiaLite layers
        :rtype: str
        """
        datasource = self.qgs_layer.source()
        serverDatasource = makeDatasource(datasource, self.layerType)

        new_datasource = serverDatasource if serverDatasource is not None else datasource

        pre_err_msg = ""

        if self.qgs_layer.type() != QgsMapLayer.VectorLayer:
            return new_datasource

        # fix new datasource
        self.qgs_layer.setDataSource(new_datasource, self.qgs_layer.name(), self.qgs_layer.dataProvider().name())

        if not self.qgs_layer.isValid():
            logging.warning("Layer id %s is not valid in QGIS project file: %s" % (
            self.layerId, self.qgisProject.qgisProjectFile.name))
            msg = _("Current datasource is {}").format(new_datasource)
            raise Exception(f'{pre_err_msg}: {msg}')

        return new_datasource

    def _getDataAliases(self):
        """
        Get properties fields aliasies
        :return: A dict key:value of layer attributes name.
        :rtype: dict
        """

        ret = OrderedDict()

        if self.qgs_layer.type() != QgsMapLayer.VectorLayer:
            return ret

        for f in self.qgs_layer.fields():
            ret[f.name()] = f.displayName()
        return ret

    def _getDataColumns(self):
        """
        Retrieve data about columns for db table or ogr layer type
        [
            {
                'name': '<name>',
                'type': '<data_type>',
                'label': '<label>',
            },
            ...
        ]
        :return: A dict list with data attributes structure.
        :rtype: list
        """

        if self.qgs_layer.type() != QgsMapLayer.VectorLayer:
            return None

        columns = []
        for f in self.qgs_layer.fields():
            columns.append({
                'name': f.name(),
                'type': QVariant.typeToName(f.type()).upper(),
                'label': f.displayName(),
            })

        return columns


    def _addAliesToColumns(self, columns):
        """
        Add aliases to column original name
        :param columns: dict layer structure columns
        """

        for column in columns:
            if column['name'] in self.aliases:
                column['label'] = self.aliases[column['name']] if self.aliases[column['name']] != "" else column['name']

    def _getDataExcludeAttributesWMS(self):
        """
        Get attribute to exclude from WMS info and relations
        :return: a list of columns excluded from WMS services and relations
        :rtype: list
        """

        try:
            return list(self.qgs_layer.excludeAttributesWms())
        except Exception as e:
            return []

    def _getDataExcludeAttributesWFS(self):
        """
        Get attribute to exclude from WMS info and relations
        :return: a list of columns excluded from WMS services and relations
        .rtype: list
        """

        try:
            return list(self.qgs_layer.excludeAttributesWfs())
        except Exception as e:
            return []

    def _getDataEditTypes(self):
        """
        Get edittypes for editing widget
        {
            '<field_name>': {
                    'widgetv2type': <qgis edit widget type>,
                    'fieldEditable': <field editable boolean value>,
                    'values': <possible map wigdet value>
            }
        }
        :return: dict of field name key of qgis widgets
        :rtype: dict
        """

        edittype_columns = dict()

        # only for VectorLayer
        if self.qgs_layer.type() != QgsMapLayer.VectorLayer:
            return edittype_columns

        fields = self.qgs_layer.fields()
        eformconf = self.qgs_layer.editFormConfig()
        for field in fields:
            idx = fields.indexFromName(field.name())

            # get field widget data
            ewidget = self.qgs_layer.editorWidgetSetup(idx)

            data = {
                'widgetv2type': ewidget.type(),
                'fieldEditable': '0' if eformconf.readOnly(idx) else '1',
                'values': list()
            }

            options = ewidget.config()
            if ewidget.type() == 'ValueMap':
                if 'map' in options:
                    if isinstance(options['map'], dict):
                        for key, value in options['map'].items():
                            data['values'].append({'key': key, 'value': value})
                    else:
                        #case list
                        for item in options['map']:
                            for key, value in item.items():
                                data['values'].append({'key': key, 'value': value})
            else:
                data.update(options)

            edittype_columns[field.name()] = data

        return edittype_columns

    def _getDataEditorlayout(self):
        """
        Get QGIS editor layout
        :return: layout type
        :rtype: str, None
        """
        layouts = {
            QgsEditFormConfig.GeneratedLayout: 'generallayout',
            QgsEditFormConfig.TabLayout: 'tablayout',
            QgsEditFormConfig.UiFileLayout: 'unfilelayout'
        }

        try:
            return layouts[self.qgs_layer.editFormConfig().layout()]
        except:
            return None

    def _getDataEditorformstructure(self):
        """
        Get qgis attribute editor form if editor layout is not generatedlayout
        For now only tablayout management
        :return: form structure
        :rtype: dict, None
        """

        if self.editorlayout == 'tablayout':

            tabs = self.qgs_layer.editFormConfig().tabs()

            def build_form_tree_object(elements):
                to_ret_form_structure = []
                for element in elements:

                    to_ret_node = {
                        'name': element.name(),
                        'showlabel': element.showLabel()
                    }

                    if element.type() == QgsAttributeEditorElement.AeTypeContainer:

                        to_ret_node.update({
                            'groupbox': element.isGroupBox(),
                            'columncount': element.columnCount(),
                            'nodes': build_form_tree_object(element.children())
                        })

                    if element.type() == QgsAttributeEditorElement.AeTypeField:
                        to_ret_node.update({
                            'index': element.idx(),
                            'field_name': element.name()
                        })
                        if to_ret_node['name'] in self.aliases:
                            to_ret_node.update({'alias': self.aliases[to_ret_node['name']]})
                        del(to_ret_node['name'])

                    to_ret_form_structure.append(to_ret_node)
                return to_ret_form_structure

            return build_form_tree_object(tabs)

        else:
            return None

    def _getDataExtent(self):
        """Get layer extension"""

        return self.qgs_layer.extent().asWktPolygon()

    def clean(self):
        for validator in self.validators:
            validator.clean()

    def save(self):
        """
        Save o update layer instance into db
        """

        columns = json.dumps(self.columns) if self.columns else None
        excludeAttributesWMS = json.dumps(self.excludeAttributesWMS) if self.excludeAttributesWMS else None
        excludeAttributesWFS = json.dumps(self.excludeAttributesWFS) if self.excludeAttributesWFS else None

        self.instance, created = self._layer_model.objects.get_or_create(
            #origname=self.origname,
            qgs_layer_id=self.layerId,
            project=self.qgisProject.instance,
            defaults={
                'origname': self.origname,
                'name': self.name,
                'title': self.title,
                'is_visible': self.isVisible,
                'layer_type': self.layerType,
                'qgs_layer_id': self.layerId,
                'min_scale': self.minScale,
                'max_scale': self.maxScale,
                'scalebasedvisibility': self.scaleBasedVisibility,
                'database_columns': columns,
                'srid': self.srid,
                'datasource': self.datasource,
                'order': self.order,
                'edit_options': self.editOptions,
                'wfscapabilities': self.wfsCapabilities,
                'exclude_attribute_wms': excludeAttributesWMS,
                'exclude_attribute_wfs': excludeAttributesWFS,
                'geometrytype': self.geometrytype,
                'vectorjoins': self.vectorjoins,
                'edittypes': self.editTypes,
                'editor_layout': self.editorlayout,
                'editor_form_structure': self.editorformstructure,
                'extent': self.extent
                }
            )

        if not created:
            self.instance.name = self.name
            self.instance.title = self.title
            self.instance.is_visible = self.isVisible
            self.instance.layer_type = self.layerType
            self.instance.qgs_layer_id = self.layerId
            self.instance.min_scale = self.minScale
            self.instance.max_scale = self.maxScale
            self.instance.scalebasedvisibility = self.scaleBasedVisibility
            self.instance.datasource = self.datasource
            self.instance.database_columns = columns
            self.instance.srid = self.srid
            self.instance.order = self.order
            self.instance.edit_options = self.editOptions
            self.instance.wfscapabilities = self.wfsCapabilities
            self.instance.exclude_attribute_wms = excludeAttributesWMS
            self.instance.exclude_attribute_wfs = excludeAttributesWFS
            self.instance.geometrytype = self.geometrytype
            self.instance.vectorjoins = self.vectorjoins
            self.instance.edittypes = self.editTypes
            self.instance.editor_layout = self.editorlayout
            self.instance.editor_form_structure = self.editorformstructure
            self.instance.extent = self.extent

        # Save self.instance
        self.instance.save()


class QgisProject(XmlData):
    """
    A qgis xml project file wrapper
    """

    _dataToSet = [
        'name',
        'title',
        'srid',
        'units',
        'qgisVersion',
        'initialExtent',
        'maxExtent',
        'wmsuselayerids',
        'wfsLayers',
        'wfstLayers',
        'layersTree',
        'layers',
        'layerRelations',
        'layouts'
        ]

    _defaultValidators = [
        IsGroupCompatibleValidator,
        ProjectExists,
        ProjectTitleExists,
        UniqueLayername,
        CheckMaxExtent
    ]

    _pre_exception_message = 'Project'

    #_regexXmlLayer = 'projectlayers/maplayer[@geometry!="No geometry"]'

    _regexXmlLayer = 'projectlayers/maplayer'

    # for QGIS2
    _regexXmlComposer = 'Composer'
    _regexXmlComposerPicture = 'Composition/ComposerPicture'

    #for QGIS3
    _regexXmlLayouts = 'Layouts/Layout'
    _regexXmlLayoutItems = 'LayoutItem'

    _project_model = Project

    _qgisprojectlayer_class = QgisProjectLayer

    def __init__(self, qgis_file, **kwargs):
        self.qgisProjectFile = qgis_file
        self.validators = []
        self.instance = None

        #istance of a model Project
        if 'instance' in kwargs:
            self.instance = kwargs['instance']

        if 'group' in kwargs:
            self.group = kwargs['group']

        for k in ['thumbnail', 'description', 'baselayer']:
            setattr(self, k, kwargs[k] if k in kwargs else None)


        # try to load xml project file
        self.loadProject(**kwargs)

        # set data value into this object
        self.setData()

        self.closeProject(**kwargs)

        #register defaul validator
        for validator in self._defaultValidators:
            self.registerValidator(validator)

    def loadProject(self, **kwargs):
        """
        Load project file by xml parser and instance a QgsProject object
        """
        try:

            # we have to rewind the underlying file in case it has been already parsed
            self.qgisProjectFile.file.seek(0)
            self.qgisProjectTree = lxml.parse(self.qgisProjectFile, forbid_entities=False)

        except Exception as e:
            raise QgisProjectException(_('The project file is malformed: {}').format(e.args[0]))

        # set a global QgsProject object
        self.qgs_project = QgsProject()

        # Case FieldFile
        if hasattr(self.qgisProjectFile, 'path'):
            project_file = self.qgisProjectFile.path

        # Case UploadedFileWithId
        elif hasattr(self.qgisProjectFile, 'file'):
            if hasattr(self.qgisProjectFile.file, 'path'):
                project_file = self.qgisProjectFile.file.path
            else:
                project_file = self.qgisProjectFile.file.name

        # Default case
        else:
            project_file = self.qgisProjectFile.name

        # Read canvas settings
        self.mapCanvas = QgsMapCanvas()

        def _readCanvasSettings(xmlDocument):
            self.mapCanvas.readProject(xmlDocument)

        self.qgs_project.readProject.connect(
            _readCanvasSettings, Qt.DirectConnection)

        if not self.qgs_project.read(project_file):
            raise QgisProjectException(_('Could not read QGIS project file: {}').format(project_file))

    def closeProject(self, **kwargs):
        """
        Close QgsProject object.
        Is important to avoid locking data like GeoPackage.
        """

        del(self.qgs_project)

    def _getDataName(self):
        """
        Get QgsProject title property per projectname xml property
        :rtype: str
        """
        return self.qgs_project.title()

    def _getDataTitle(self):
        """
        Get QgsProject title property
        :return: project title property
        :rtype: str
        """
        return self.qgs_project.title()

    def _getDataInitialExtent(self):
        """
        Get start QGIS project extension
        :return: Start project extension
        :rtype: dict
        """
        extent = self.mapCanvas.extent()
        return {
            'xmin': extent.xMinimum(),
            'ymin': extent.yMinimum(),
            'xmax': extent.xMaximum(),
            'ymax': extent.yMaximum(),
        }

    def _getDataMaxExtent(self):
        """
        Get max QGIS extension project
        :return: Max extension project
        :rtype: dict
        """
        wmsExtent = QgsServerProjectUtils.wmsExtent(self.qgs_project)
        if wmsExtent is not wmsExtent.isNull() and wmsExtent != QgsRectangle():
            return {
                'xmin': wmsExtent.xMinimum(),
                'ymin': wmsExtent.yMinimum(),
                'xmax': wmsExtent.xMaximum(),
                'ymax': wmsExtent.yMaximum()
            }
        else:
            return None

    def _getDataWmsuselayerids(self):
        """
        Get WMSUseLayerIDS property
        :return: boolean WMSUseLayerIDS property
        :rtype: bool
        """
        return QgsServerProjectUtils.wmsUseLayerIds(self.qgs_project)

    def _getDataSrid(self):
        """
        Get map SRID
        :return: Map SRID
        :rtype: int
        """
        return self.qgs_project.crs().postgisSrid()

    def _getDataUnits(self):
        """
        Get map units
        :return: Map units
        :rtype: str
        """
        return QgsUnitTypes().encodeUnit(self.qgs_project.crs().mapUnits())

    def _checkLayerTypeCompatible(self, layerTree):
        """
        Check il layer is compatible for to show in webgis
        :param layerTree: dict QGIS layer tree structure
        :return: boolean compatibility
        .:rtype: bool
        """
        if 'name' in layerTree.attrib:
            if layerTree.attrib['name'] == 'openlayers':
                return False
        if 'embedded' in layerTree.attrib:
            if layerTree.attrib['embedded'] == '1':
                return False
        return True

    def _getDataLayersTree(self):
        """
        Build layers tree structure (TOC)
        :return: layer tree structure with options
        :rtype: dict
        """

        def buildLayerTreeNodeObject(layerTreeNode):

            toRetLayers = []
            for node in layerTreeNode.children():

                toRetLayer = {
                    'name': node.name(),
                    'expanded': node.isExpanded()
                }

                try:
                    # try for layer node
                    toRetLayer.update({
                        'id': node.layerId(),
                        'visible': node.layer() in node.checkedLayers()
                    })

                except:

                    toRetLayer.update({
                        'mutually-exclusive': node.isMutuallyExclusive(),
                        'nodes': buildLayerTreeNodeObject(node),
                        'checked': node.isVisible(),

                    })

                toRetLayers.append(toRetLayer)
            return toRetLayers

        return buildLayerTreeNodeObject(self.qgs_project.layerTreeRoot())

    def _getDataLayers(self):
        """
        Get QGIS project layers
        :return: list of QgsProjectLayer instances
        :rtype: list
        """
        layers = []

        for layerid, layer in self.qgs_project.mapLayers().items():
            layers.append(self._qgisprojectlayer_class(layer, qgisProject=self))
        return layers

    def _getDataLayerRelations(self):
        """
        Get relations layer section into project
        :return: layer relations dict settings
        :rtype: dict, None
        """
        # get root of layer-tree-group
        relations = self.qgs_project.relationManager().relations()
        if len(relations) == 0:
            return None

        layer_realtions = []
        strength_type = {
            0: 'Association',
            1: 'Composition'
        }
        for relation_id, relation in relations.items():
            attrib = {
                'id': relation_id,
                'name': relation.name(),
                'strength': strength_type[relation.strength()],
                'referencedLayer': relation.referencedLayerId(),
                'referencingLayer': relation.referencingLayerId(),
            }
            # get only first pair relation
            # FIXME: save every field pair
            field_refs = []
            for referencingField, referencedField in relation.fieldPairs().items():
                field_refs.append([referencingField, referencedField])
            attrib.update({
                'fieldRef': {
                    'referencingField': field_refs[0][0],
                    'referencedField': field_refs[0][1]
                }
            })

            layer_realtions.append(attrib)
        return layer_realtions

    def _getDataLayouts(self):
        """
        Get project layouts (print and others)
        :return: project layouts dict settings
        :rtype: dict, None
        """

        layouts = []
        qgs_layouts = self.qgs_project.layoutManager().layouts()
        for qgs_layout in qgs_layouts:
            if qgs_layout.layoutType() == QgsMasterLayoutInterface.PrintLayout:

                # find first page into items
                first_page_size = qgs_layout.pageCollection().pages()[0].pageSize()

                # retrieve dims and name information
                p_playout = {
                    'name': qgs_layout.name(),
                    'w': first_page_size.width(),
                    'h': first_page_size.height()
                }

                # check if is a ATLAS print
                qgs_atlas = qgs_layout.atlas()
                atlas_field_name = qgs_atlas.pageNameExpression()[1:-1]
                if atlas_field_name == '':
                    atlas_field_name = None
                if qgs_atlas.enabled():
                    p_playout.update({
                        'atlas': {
                            'qgs_layer_id': qgs_atlas.coverageLayer().id(),
                            'field_name': atlas_field_name
                        }
                    })

                    # if atlas_field_name is None, give max feature
                    if not atlas_field_name:
                        p_playout['atlas']['feature_count'] = count_qgis_features(qgs_atlas.coverageLayer())

                # add items
                maps = []
                count = 0
                for item in qgs_layout.items():
                    if isinstance(item, QgsLayoutItemMap):

                        brect = item.boundingRect()
                        extent = item.extent()
                        map = {
                            'name': f'map{count}',
                            'displayname': item.displayName(),
                            'w': brect.right() - brect.left(),
                            'h': brect.bottom() - brect.top(),
                            'overview': item.overview().linkedMap() != None and item == item.overview().map(),
                            'scale': item.scale(),
                            'extent': {
                                'xmin': extent.xMinimum(),
                                'ymin': extent.yMinimum(),
                                'xmax': extent.xMaximum(),
                                'ymax': extent.yMaximum()
                            }
                        }

                        maps.append(map)

                        count += 1

                p_playout.update({'maps': maps})
                layouts.append(p_playout)

        return json.dumps(layouts)


    def _getDataQgisVersion(self):
        """
        Get QGIS project version
        :return: QGIS project version
        :rtype: str
        """

        # FIXME: is not possibile by QGIS API at the moment.
        return self.qgisProjectTree.getroot().attrib['version']

    def _getDataWfsLayers(self):
        """
        Return WFS layers
        :return: a list of layers set as WFS
        :rtype: list
        """

        return QgsServerProjectUtils.wfsLayerIds(self.qgs_project)

    def _getDataWfstLayers(self):
        """
        Return WFST layers
        :return: a dict of layers set as WFS with editing options
         {
            'INSERT': [...],
            'UPDATE': [...],
            'DELETE': [...]
        }
        :rtype: list
        """

        return{
            'INSERT': QgsServerProjectUtils.wfstInsertLayerIds(self.qgs_project),
            'UPDATE': QgsServerProjectUtils.wfstUpdateLayerIds(self.qgs_project),
            'DELETE': QgsServerProjectUtils.wfstDeleteLayerIds(self.qgs_project)
        }

    def clean(self):
        for validator in self.validators:
            validator.clean()

        for layer in self.layers:
            layer.clean()

    def save(self, instance=None, **kwargs):
        """
        Save or update  qgisporject and layers into db.
        Update QGIS project file with new datasources for ogr/gdal and sqlite types.
        :param instance: Project instance
        """

        with transaction.atomic():
            if not instance and not self.instance:

                thumbnail = kwargs.get('thumbnail')
                description = kwargs.get('description')
                baselayer = kwargs.get('baselayer')

                self.instance = self._project_model.objects.create(
                    qgis_file=self.qgisProjectFile,
                    group=self.group,
                    title=self.title,
                    initial_extent=self.initialExtent,
                    max_extent=self.maxExtent,
                    wms_use_layer_ids=self.wmsuselayerids,
                    thumbnail=thumbnail,
                    description=description,
                    baselayer=baselayer,
                    qgis_version=self.qgisVersion,
                    layers_tree=self.layersTree,
                    relations=self.layerRelations,
                    layouts=self.layouts
                )
            else:
                if instance:
                    self.instance = instance
                self.instance.qgis_file = self.qgisProjectFile
                self.instance.title = self.title
                self.instance.qgis_version = self.qgisVersion
                self.instance.initial_extent = self.initialExtent
                self.instance.max_extent = self.maxExtent
                self.instance.layers_tree = self.layersTree
                self.instance.relations = self.layerRelations
                self.instance.layouts = self.layouts
                self.instance.wms_use_layer_ids = self.wmsuselayerids

                self.instance.save()

            # Create or update layers
            for l in self.layers:
                l.save()

            # Pre-existing layers that have not been updated must be dropped
            newLayerNameList = [(layer.name, layer.layerId, layer.datasource) for layer in self.layers]
            for layer in self.instance.layer_set.all():
                if (layer.name, layer.qgs_layer_id, layer.datasource) not in newLayerNameList:
                    layer.delete()

            # Update qgis file datasource for SpatiaLite and OGR layers
            self.updateQgisFileDatasource()

    def updateQgisFileDatasource(self):
        """Update qgis file datasource for SpatiaLite and OGR layers.

        SpatiaLite and OGR layers need their datasource string to be
        modified at import time so that the original path is replaced with
        the DjangoQGIS one (which is stored in ``settings.py`` as variable
        ``DATASOURCE_PATH``).

        Example original datasource::

        <datasource>\\SIT-SERVER\sit\charts\definitivo\d262120.shp</datasource>

        Example modified datasource::

        <datasource>/home/sit/charts\definitivo\d262120.shp</datasource>
        """

        # Parse the file and build the XML tree
        self.instance.qgis_file.file.seek(0)
        tree = lxml.parse(self.instance.qgis_file, forbid_entities=False)

        # Run through the layer trees
        for layer in tree.xpath(self._regexXmlLayer):
            if self._checkLayerTypeCompatible(layer):
                layerType = layer.find('provider').text
                datasource = layer.find('datasource').text

                newDatasource = makeDatasource(datasource, layerType)

                # Update layer
                if newDatasource:
                    layer.find('datasource').text = newDatasource

        # update file of print composers
        for composer in tree.xpath(self._regexXmlComposer):
            for composer_picture in composer.xpath(self._regexXmlComposerPicture):
                composer_picture.attrib['file'] = makeComposerPictureFile(composer_picture.attrib['file'])

        # for qgis3 try to find Layout/LayoutItem
        for layout in tree.xpath(self._regexXmlLayouts):
            for layoutitem in layout.xpath(self._regexXmlLayoutItems):
                if 'file' in layoutitem.attrib:
                    layoutitem.attrib['file'] = makeComposerPictureFile(layoutitem.attrib['file'])

        # Update QGIS file
        tree.write(self.instance.qgis_file.path, encoding='UTF-8')


class QgisProjectSettingsWMS(XmlData):
    """ Wraper-parsing QGIS WMS projectsettings service """

    _dataToSet = [
        'metadata',
        'layers',
        'composerTemplates'
    ]

    _NS = {
        'opengis': 'http://www.opengis.net/wms',
        'xlink': 'http://www.w3.org/1999/xlink'
    }

    _pre_exception_message = 'QGISProjectSettings'

    def __init__(self, project_settings, **kwargs):
        self.qgisProjectSettingsFile = project_settings

        # load data
        self.loadProjectSettings()

        # set data
        self.setData()

    def loadProjectSettings(self):
        """
        Load from 'string'  wms response request getProjectSettings
        :return:
        """
        try:
            self.qgisProjectSettingsTree = lxml.fromstring(self.qgisProjectSettingsFile)
        except Exception as e:
            raise Exception(
                _('The project settings is malformed: {} ----- {}'.format(e.args[0], self.qgisProjectSettingsFile)))

    def _buildTagWithNS(self, tag):
        """
        Build Tag with Name Space 'opengis' for XNl searching
        :param tag: str xml tag name
        :return: search string
        :rtype: str
        """

        return '{{{0}}}{1}'.format(self._NS['opengis'], tag)

    def _buildTagWithNSXlink(self, tag):
        """
        Build Tag with Name Space 'xlink' for XNl searching
        :param tag: str xml tag name
        :return: search string
        :rtype: str
        """
        return '{{{0}}}{1}'.format(self._NS['xlink'], tag)

    def _getBBOXLayer(self, layerTree):
        """
        Get BBOX for every CRS available
        :param layerTree: dict layers tree structure
        :return: a dict of BBOX coordinates for every CRS
        :rtype: dict
        """
        bboxes = {}

        bboxTrees = layerTree.xpath(
            'opengis:BoundingBox',
            namespaces=self._NS
        )

        for bboxTree in bboxTrees:
            bboxes[bboxTree.attrib['CRS']] = {
                'minx': float(bboxTree.attrib['minx']),
                'miny': float(bboxTree.attrib['miny']),
                'maxx': float(bboxTree.attrib['maxx']),
                'maxy': float(bboxTree.attrib['maxy']),
            }

        return bboxes

    def _getLayerTreeData(self, layerTree):
        """
        Build a layers tree structure with attributes for every layer.
        Add informations like legend, alias name, metedata etc.
        :param layerTree: XmlTree object
        :return: a layers tree dict structure
        :rtype: dict
        """

        subLayerTrees = layerTree.xpath('opengis:Layer', namespaces=self._NS)
        if subLayerTrees:
            for subLayerTree in subLayerTrees:
                self._getLayerTreeData(subLayerTree)
        else:
            name = layerTree.find(self._buildTagWithNS('Name')).text
            attributes = layerTree.find(self._buildTagWithNS('Attributes'))
            attrs = []
            if attributes is not None and len(attributes):
                for attribute in attributes:
                    attribs = attribute.attrib
                    if 'alias' not in attribs:
                        attribs['alias'] = ''
                    attrs.append(attribs)

            CRS = layerTree.xpath('opengis:CRS', namespaces=self._NS)

            # QGIS3 no set queryable attributo for layer groups
            queryable = False
            if 'queryable' in layerTree.attrib:
                queryable = bool(int(layerTree.attrib['queryable']))

            dataLayer = {
                'name': name,
                'queryable': queryable,
                'bboxes': self._getBBOXLayer(layerTree),
                'styles': [],
                'metadata': {
                    'title': layerTree.find(self._buildTagWithNS('Title')).text,
                    'attributes': attrs,
                    'crs': [crs.text for crs in CRS] if CRS else None,
                }
            }

            # add STYLE
            styles = layerTree.xpath('opengis:Style', namespaces=self._NS)
            for style in styles:
                style_toadd = {
                    'name': style.find(self._buildTagWithNS('Name')).text,
                    'title': style.find(self._buildTagWithNS('Title')).text
                }

                # add legendurl if is set
                try:
                    legendurl = style.find(self._buildTagWithNS('LegendURL'))
                    style_toadd['legendulr'] = {}
                    try:
                        style_toadd['legendulr']['format'] = legendurl.find(
                            self._buildTagWithNS('Format')).text
                    except:
                        pass

                    try:
                        style_toadd['legendulr']['onlineresources'] = \
                            legendurl.find(self._buildTagWithNS('OnlineResource')).attrib[
                                self._buildTagWithNSXlink('href')]
                    except:
                        pass
                except:
                    pass

                dataLayer['styles'].append(style_toadd)



            # add keywords
            try:
                keywords = layerTree.find(self._buildTagWithNS('KeywordList'))\
                    .xpath('opengis:Keyword', namespaces=self._NS)
                dataLayer['metadata'].update({
                    'keywords': [k.text for k in keywords]
                })
            except:
                pass




            # add attribution
            try:
                dataurl = layerTree.find(self._buildTagWithNS('DataURL'))
                dataLayer['metadata'].update({
                    'dataurl': {}
                })

                try:
                    dataLayer['metadata']['dataurl']['format'] = dataurl.find(
                        self._buildTagWithNS('Format')).text
                except:
                    pass

                try:
                    dataLayer['metadata']['dataurl']['onlineresources'] = \
                        dataurl.find(self._buildTagWithNS('OnlineResource')).attrib[
                            self._buildTagWithNSXlink('href')]
                except:
                    pass
            except:
                pass

            # add MetadataURL
            try:
                metadataurl = layerTree.find(self._buildTagWithNS('MetadataURL'))
                dataLayer['metadata'].update({
                    'metadataurl': {}
                })

                try:
                    dataLayer['metadata']['metadataurl']['format'] = metadataurl.find(
                        self._buildTagWithNS('Format')).text
                except:
                    pass

                try:
                    dataLayer['metadata']['metadataurl']['onlineresources'] = \
                        metadataurl.find(self._buildTagWithNS('OnlineResource')).attrib[
                            self._buildTagWithNSXlink('href')]
                except:
                    pass
            except:
                pass

            # add attribution
            try:
                attribution = layerTree.find(self._buildTagWithNS('Attribution'))
                dataLayer['metadata'].update({
                    'attribution': {}
                })

                try:
                    dataLayer['metadata']['attribution']['title'] = attribution.find(self._buildTagWithNS('Title')).text
                except:
                    pass

                try:
                    dataLayer['metadata']['attribution']['onlineresources'] = \
                        attribution.find(self._buildTagWithNS('OnlineResource')).attrib[
                            self._buildTagWithNSXlink('href')]
                except:
                    pass
            except:
                pass

            # add abstract
            try:
                dataLayer['metadata']['abstract'] = layerTree.find(self._buildTagWithNS('Abstract')).text,
            except:
                pass

            if 'visible' in layerTree.attrib:
                dataLayer['visible'] = bool(int(layerTree.attrib['visible']))

            self._layersData[name] = dataLayer

    def _getDataMetadata(self):
        """
        Get metadata project informations.
        :return: Project metadata info.
        .:rtype: dict
        """
        # add simple tags
        self._metadata = {}

        try:
            service = self.qgisProjectSettingsTree.xpath(
                'opengis:Service',
                namespaces=self._NS
            )[0]
        except:
            return self._metadata


        for tag in ('Name',
                    'Title',
                    'Abstract',
                    'Fees',
                    'AccessConstraints'):
            try:
                self._metadata.update({
                    tag.lower(): service.find(self._buildTagWithNS(tag)).text
                })
            except:
                pass


        # add keywords
        keywords = service.find(self._buildTagWithNS('KeywordList')).xpath('opengis:Keyword', namespaces=self._NS)
        self._metadata.update({
            'keywords': [k.text for k in keywords]
        })

        # for OnlineResources
        try:
            self._metadata['onlineresource'] = \
                service.find(self._buildTagWithNS('OnlineResource')).attrib[
                    self._buildTagWithNSXlink('href')]
        except:
            pass

        # add contact informations
        contactinfo = service.find(self._buildTagWithNS('ContactInformation'))
        try:
            contactperson = contactinfo.find(self._buildTagWithNS('ContactPersonPrimary'))
        except:
            pass

        self._metadata.update(OrderedDict({
            'contactinformation': OrderedDict({
                'personprimary': {},
            })
        }))

        try:
            self._metadata['contactinformation'].update(OrderedDict({
                    'contactvoicetelephone': contactinfo.find(self._buildTagWithNS('ContactVoiceTelephone')).text,
                    'contactelectronicmailaddress': contactinfo.find(
                        self._buildTagWithNS('ContactElectronicMailAddress')).text,
                }))
        except:
            pass

        for tag in ('ContactPerson', 'ContactOrganization', 'ContactPosition'):
            try:
                self._metadata['contactinformation']['personprimary'].update({
                    tag.lower(): contactperson.find(self._buildTagWithNS(tag)).text
                })
            except:
                pass

        return self._metadata

    def _getDataLayers(self):
        """
        Get layers info as structure metadata end other.
        :return: Layers data and metadata
        :rtype: dict
        """

        self._layersData = {}

        layersTree = self.qgisProjectSettingsTree.xpath(
            'opengis:Capability',
            namespaces=self._NS
        )

        self._getLayerTreeData(layersTree[0])
        return self._layersData

    def _getDataComposerTemplates(self):
        """
        Get print composer data
        :return: list of print layout available.
        :rtype: list
        """

        self._composerTemplatesData = []

        composerTemplates= self.qgisProjectSettingsTree.xpath(
            'opengis:Capability/opengis:ComposerTemplates/opengis:ComposerTemplate',
            namespaces=self._NS
        )

        _composerTemplateData = {}
        for composerTemplate in composerTemplates:
            _composerTemplateData['name'] = composerTemplate.attrib['name']
            _composerMaps = []
            for composerMap in composerTemplate.findall("opengis:ComposerMap", namespaces=self._NS):
              _composerMaps.append({
                  'name': composerMap.attrib['name'],
                  'w': float(composerMap.attrib['width']),
                  'h': float(composerMap.attrib['height'])
              })
            self._composerTemplatesData.append({
                'name': composerTemplate.attrib['name'],
                'w': composerTemplate.attrib['width'],
                'h': composerTemplate.attrib['height'],
                'maps': _composerMaps
            })

        return self._composerTemplatesData


class QgisPgConnection(object):
    """
    Postgis xml interchange file
    """
    _version = "1.0"

    _params = {
        'port': 5432,
        'saveUsername': 'true',
        'password': '',
        'savePassword': 'true',
        'sslmode': 1,
        'service': '',
        'username': '',
        'host': '',
        'database': '',
        'name': '',
        'estimatedMetadata': 'false'
    }

    def __init__(self, **kwargs):

        self._data = {}
        for k,v in list(kwargs.items()):
            setattr(self, k, v)

    def __setattr__(self, key, value):

        if key in list(QgisPgConnection._params.keys()):
            self.__dict__['_data'][key] = value
        else:
            self.__dict__[key] = value

    def __getattr__(self, key):

        if key in list(QgisPgConnection._params.keys()):
            try:
                return self.__dict__['_data'][key]
            except:
                return QgisPgConnection._params[key]

        return self.__dict__[key]

    def asXML(self):

        qgsPgConnectionTree = etree.Element('qgsPgConnections', version=self._version)
        postgisTree = etree.Element('postgis')
        postgisTreeAttributes = postgisTree.attrib

        for key in list(QgisPgConnection._params.keys()):
            postgisTreeAttributes[key] = str(getattr(self, key))

        qgsPgConnectionTree.append(postgisTree)

        return etree.tostring(qgsPgConnectionTree, doctype='<!DOCTYPE connections>')


