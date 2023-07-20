import semantic_version

__version__ = str(semantic_version.Version('1.0.0'))


version_spec = semantic_version.SimpleSpec('~=1.0.0')  # Any release between 1.0 and 1.1
