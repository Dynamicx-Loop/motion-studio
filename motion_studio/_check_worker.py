"""Private isolated unittest loader, keeping package-relative script tests valid."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import unittest


if __name__ == '__main__':
    source, root = map(Path, sys.argv[1:3])
    sys.path[:0] = [str(root), str(root / 'scripts'), str(source.parent)]
    name = '.'.join(source.relative_to(root).with_suffix('').parts)
    spec = spec_from_file_location(name, source)
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    if not suite.countTestCases():
        sys.exit('No tests loaded from ' + str(source))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
