"""Opt-in pinned robot/sample library smoke checks."""
CHECK_TIER = 'robot-static'
CHECK_MODULES = ('numpy', 'mujoco')
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


from test_studio_assets import uploaded, XML

@unittest.skipUnless(PYTHON.is_file(),'independent MuJoCo runtime unavailable')
class LibraryRuntimeTests(unittest.TestCase):
    def test_browser_xml_and_zip_uploads_are_immutable_and_selectable(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio=Studio(Path(tmp))
            asset=studio.upload_robot([uploaded('folder/robot.xml')])
            self.assertEqual(studio.robot_file(asset.asset_id,'source/provenance/original/folder/robot.xml').read_bytes(),XML)
            archive=io.BytesIO()
            with zipfile.ZipFile(archive,'w') as z:z.writestr('robot.xml',XML)
            zipped=studio.upload_robot([uploaded('robot.zip',archive.getvalue())])
            self.assertEqual(studio.robot_file(zipped.asset_id,'source/provenance/original/robot.xml').read_bytes(),XML)
            run=studio.create_draft('Uploaded robot')
            selected=studio.save_robot_pose(run.run_id,asset.asset_id,name='Reference',qpos=asset.default_qpos,torso_body=asset.root_body)
            self.assertEqual(selected.robot_asset_id,asset.asset_id)
            with serving(studio) as server:
                code,_,body=request(server,'POST','/api/robot-upload',json.dumps({'files':[uploaded('robot.xml')],'entry_path':'robot.xml','derive_free_root':False}),{'Content-Type':'application/json'})
                self.assertEqual(code,201,body)

    def test_uploaded_sibling_meshes_and_includes_are_confined_and_originals_preserved(self):
        mesh=b'v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\nf 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n'
        main=b'<mujoco><compiler meshdir="../meshes"/><asset><mesh name="shape" file="tetra.obj"/></asset><worldbody><body name="base"><freejoint/><geom type="mesh" mesh="shape"/><include file="../parts/arm.xml"/></body></worldbody></mujoco>'
        part=b'<mujocoinclude><body name="arm"><joint name="hinge" range="-90 90"/><geom type="sphere" size=".1"/></body></mujocoinclude>'
        with tempfile.TemporaryDirectory() as tmp:
            studio=Studio(Path(tmp))
            asset=studio.upload_robot([uploaded('model/robot.xml',main),uploaded('meshes/tetra.obj',mesh),uploaded('parts/arm.xml',part)],entry_path='model/robot.xml')
            self.assertEqual(studio.robot_file(asset.asset_id,'source/provenance/original/model/robot.xml').read_bytes(),main)
            self.assertEqual(studio.robot_file(asset.asset_id,'source/provenance/original/meshes/tetra.obj').read_bytes(),mesh)
            self.assertEqual([j.name for j in asset.joints],['hinge'])
            # The same parent escape outside the explicit uploaded root fails.
            with self.assertRaises(StudioError):
                studio.upload_robot([uploaded('robot.xml',main),uploaded('meshes/tetra.obj',mesh),uploaded('parts/arm.xml',part)],entry_path='robot.xml')

    def test_all_four_official_robots_compile_and_named_poses_satisfy_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            studio=Studio(Path(tmp))
            for key in ('g1','k1','piplus','t800'):
                with self.subTest(key=key):
                    result=studio.add_builtin_robot(key);asset=result['asset'];pose=result['pose']
                    preview=studio.preview_robot(asset['asset_id'],pose['qpos'])
                    self.assertGreater(len(preview['transforms']),10)
                    self.assertIn(pose['torso_body'],asset['bodies'])
                    if key in ('piplus','t800'):
                        self.assertIn('source/provenance/original.xml',asset['files'])
                        self.assertIn('source/provenance/derivation.json',asset['files'])
                        from motion_studio.integrations.umr_assets import robot_source
                        from motion_studio.studio._robot_assets import runtime
                        source,_=robot_source(studio.native_adapter.checkout,key)
                        original=runtime(studio.robot_python,{'operation':'preview','model':str(source),'qpos':pose['qpos']})
                        import numpy as np
                        for expected,actual in zip(original['transforms'],preview['transforms']):
                            np.testing.assert_allclose(actual['position'],expected['position'],atol=1e-12,rtol=0)
                            np.testing.assert_allclose(actual['rotation'],expected['rotation'],atol=1e-12,rtol=0)
                        self.assertEqual(len(original['transforms']),len(preview['transforms']))
            self.assertEqual(len(studio.list_robots()),4)

    def test_quick_sample_preserves_exact_source_frames_rate_and_records_trim(self):
        try:
            import numpy as np
        except ImportError:self.skipTest('NumPy unavailable')
        with tempfile.TemporaryDirectory() as tmp:
            studio=Studio(Path(tmp));asset=studio.add_sample_motion('hiphi-quick')
            self.assertLess(asset.frame_count,200)
            with np.load(studio.motion_source(asset.asset_id),allow_pickle=False) as derived:
                source=studio.native_adapter.checkout / str(derived['original_source_path'].item())
                with np.load(source,allow_pickle=False) as original:
                    stop=int(derived['source_frame_stop_exclusive'])
                    np.testing.assert_array_equal(derived['poses'],original['poses'][:stop])
                    np.testing.assert_array_equal(derived['trans'],original['trans'][:stop])
                    self.assertEqual(asset.fps,float(original['fps']))
                    self.assertEqual(int(derived['original_frame_count']),len(original['poses']))
            self.assertEqual(studio.list_runs(),())
            adapt=studio.add_sample_motion('adapt-tennis')
            self.assertEqual(adapt.up_axis,'y')
            self.assertEqual(adapt.frame_count,7745)
