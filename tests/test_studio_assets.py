"""Real library and browser-byte uploads through owned public interfaces."""
import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from motion_studio.studio import Studio, StudioError
from test_studio_robots import PYTHON
from test_studio_http import serving, request

XML = b'<mujoco><worldbody><body name="base"><freejoint/><geom type="sphere" size=".1"/><body name="arm"><joint name="joint" range="-90 90"/><geom type="box" size=".1 .1 .1"/></body></body></worldbody></mujoco>'


def uploaded(name, data=XML):
    return {'path':name, 'data':base64.b64encode(data).decode()}


class UploadValidationTests(unittest.TestCase):
    def test_escaping_duplicate_canonical_symlink_and_oversize_archives_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio = Studio(Path(tmp))
            for name in ('../robot.xml','/robot.xml','a//robot.xml','a/./robot.xml','a\\robot.xml'):
                with self.subTest(name=name), self.assertRaises(StudioError):
                    studio.upload_robot([uploaded(name)])
            with self.assertRaises(StudioError):
                studio.upload_robot([uploaded('robot.xml'), uploaded('robot.xml')])
            archive = io.BytesIO()
            with zipfile.ZipFile(archive,'w') as z:
                info=zipfile.ZipInfo('robot.xml');info.create_system=3;info.external_attr=0o120777<<16
                z.writestr(info,XML)
            with self.assertRaises(StudioError):
                studio.upload_robot([uploaded('robot.zip',archive.getvalue())])
            self.assertEqual(studio.list_robots(),())
