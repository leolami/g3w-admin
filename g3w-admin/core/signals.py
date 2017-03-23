import django.dispatch

# signal for start plugin: i.e. iternet
# data plugin to config api client from modules
initconfig_plugin_start = django.dispatch.Signal(providing_args=["projectType", "project"])

# signal to add extra maplayers attribute: i.e. iternet
post_create_maplayerattributes = django.dispatch.Signal(providing_args=["layer"])

# signal to add extra maplayers attribute: i.e. iternet
post_save_maplayer = django.dispatch.Signal(providing_args=["layer", "mode", "data"])

# signal to add extra maplayers attribute: i.e. iternet
pre_delete_maplayer = django.dispatch.Signal(providing_args=["layer", "data"])

# signal to add extra maplayers attribute: i.e. iternet
post_serialize_maplayer = django.dispatch.Signal(providing_args=["layer", "data"])

# signal after add/update map group
after_update_group = django.dispatch.Signal(providing_args=["group"])

# signal after project serialization
post_serialize_project = django.dispatch.Signal(providing_args=["app_name"])

# signal after layer serialized data on /api/config/
# send layer seralized original object and came back only dict data changed
after_serialized_project_layer = django.dispatch.Signal(providing_args=["layer"])

# signals pre update project
pre_update_project = django.dispatch.Signal(providing_args=["projectType", "project"])

# signals before delete project
before_delete_project = django.dispatch.Signal(providing_args=["app_name", "project"])

# signals pre delete project
pre_delete_project = django.dispatch.Signal(providing_args=["projectType", "project", "projects"])

# signal post project delete
post_delete_project = django.dispatch.Signal(providing_args=["projectType", "project", "projects"])

# signal after add/update project
after_update_project = django.dispatch.Signal(providing_args=["app_name", "project"])

# signal to load widgets for project
load_project_widgets = django.dispatch.Signal(providing_args=["app_name", "project"])

# signal to load actions for layer
load_layer_actions = django.dispatch.Signal(providing_args=["app_name", "layer"])

# signal send to perform search by specific module
perform_client_search = django.dispatch.Signal(providing_args=["app_name", "project_id", "widget_id"])

# signal to load specific css from module and submodules
load_css_modules = django.dispatch.Signal()

# signal to load specific js file from module and submodules
load_js_modules = django.dispatch.Signal()

# signal to load widget into dashboard
load_dashboard_widgets = django.dispatch.Signal(providing_args=["app_name"])



