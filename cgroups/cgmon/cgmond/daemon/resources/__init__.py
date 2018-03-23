import os
from cgmond.utils import load_subclasses

d = os.path.dirname(__file__)

def _load_submodule(resource_path, submodule_path, cls):

    namespace = os.path.join(resource_path, submodule_path)
    if not os.path.isdir(namespace):
        return {}

    return load_subclasses(namespace, cls)

def load_submodule(resource, cls):
    resource = resource.lower()
    path = os.path.join(d, resource)
    if not os.path.isdir(path):
        return {}

    return _load_submodule(os.path.join(d, resource), cls.__name__.lower(), cls)

def load_policies(resource):
    from cgmond.daemon.resources.interfaces import Policy
    return load_submodule(resource, Policy)

def load_usage(resource):
    from cgmond.daemon.resources.interfaces import Usage
    return load_submodule(resource, Usage)

def load_limit(resource):
    from cgmond.daemon.resources.interfaces import Limit
    return load_submodule(resource, Limit)

def load_resources():
    from cgmond.daemon.resources.interfaces import Resource
    resource_classes = {}

    for entry in os.listdir(d):
        resource_dir = os.path.join(d, entry)
        if not os.path.isdir(resource_dir):
            continue

        resource_classes.update(load_subclasses(resource_dir, Resource))

    resources = []
    for cls_name in resource_classes:
       cls =  resource_classes[cls_name]
       # Always have 'Monitor' resource first on the list
       if cls_name == 'monitor':
           resources = [cls] + resources
       else:
           resources.append(cls)

    return resources
