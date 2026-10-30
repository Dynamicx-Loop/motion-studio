"""Saved fresh export numerical gates against native MuJoCo/SMPL-X references."""
CHECK_TIER='saved-evidence'
CHECK_MODULES=('numpy','mujoco','torch')
import json
import os
from pathlib import Path
import sys
import unittest
import numpy as np
import mujoco


class StudioInspectionReferenceTests(unittest.TestCase):
    def setUp(self):
        root=os.environ.get('STUDIO_INSPECTION_SMOKE')
        if not root:
            self.skipTest('STUDIO_INSPECTION_SMOKE fresh derivative not supplied')
        self.report=json.loads((Path(root)/'inspection-smoke.json').read_text())
        self.bundle=Path(next(e['path'] for e in self.report['exports'] if e['stage']=='retargeting'))
        self.data=json.loads((self.bundle/'bindings.json').read_text())
        self.receipt=json.loads((self.bundle/'receipts.json').read_text())['retargeting']
        self.native=self.bundle/'native/retargeting'/self.receipt['attempt_id']

    def test_robot_frames_mesh_and_binding_match_independent_forward_kinematics(self):
        self.assertTrue(self.report['source_unchanged'])
        meta=self.data['motion']
        transforms=np.fromfile(self.bundle/meta['transforms'],dtype='<f4').reshape(meta['frame_count'],-1,3,4)
        with np.load(self.native/'motion.npz',allow_pickle=True) as saved:
            model=mujoco.MjModel.from_xml_path(str(saved['robot_xml'].item()))
            state=mujoco.MjData(model)
            np.testing.assert_array_equal(meta['frame_ids'],saved['frame_ids'])
            self.assertAlmostEqual(meta['fps'],saved['fps'].item(),delta=1e-6)
            local=np.asarray(meta['slot_local']); piece=np.asarray(meta['slot_piece'])
            for frame,qpos in enumerate(saved['qpos']):
                state.qpos[:]=qpos;mujoco.mj_forward(model,state)
                actual=np.einsum('nij,nj->ni',transforms[frame,piece,:,:3],local)+transforms[frame,piece,:,3]
                expected=np.empty_like(local)
                for i,part in enumerate(meta['pieces']):
                    mask=piece==i;gid=part['geom_id']
                    expected[mask]=(local[mask]@state.geom_xmat[gid].reshape(3,3).T+state.geom_xpos[gid])[:,[1,2,0]]
                np.testing.assert_allclose(actual,expected,atol=5e-7,rtol=0)

    def test_decoded_human_vertices_and_bary_slots_match_native_source(self):
        sys.path.insert(0,'/data/workspace/motion_studio/externals/UMR/scripts')
        import smpl_surface_retarget_common as common
        human=self.data['human_motion']; expected=self.receipt['inputs']
        config=json.loads((self.native/'humanoid_retarget_runtime_config.json').read_text())
        self.assertEqual(config['smplx_model_dir'],expected['motion']['model_path'])
        self.assertTrue(Path(config['smplx_model_dir']).is_file())
        collection,_=common.load_motion_collection(Path(expected['motion_file']))
        with np.load(self.native/'motion.npz',allow_pickle=True) as saved:
            key,sequence=common.select_sequence(collection,str(saved['source_sequence_key'].item()),0)
            frame_ids=saved['frame_ids'];ground=float(saved['ground_z'].item());scale=float(saved['smpl_scale'].item())
        bary=np.asarray(human['slot_bary']);slot_vertices=np.asarray(human['slot_vertices'])
        for chunk in human['chunks']:
            ids=frame_ids[chunk['start']:chunk['start']+chunk['count']]
            vertices,joints,faces=common.source_motion_vertices_joints(sequence,ids,Path(config['smplx_model_dir']),
                batch_size=32,smplx_device='cpu',smplx_batch_size=32,zero_source_finger_pose=True)
            native=common.source_points_to_retarget_frame(vertices,'smplx',sequence.get('output_up','z'))
            native[:,:,2]-=ground;native=(native*scale)[:,:,[1,2,0]]
            encoded=np.fromfile(self.bundle/chunk['file'],dtype='<i2').reshape(chunk['count'],human['vertex_count'],3)
            roots=np.asarray(human['root_positions'][chunk['start']:chunk['start']+chunk['count']])
            decoded=encoded.astype(float)*human['quantization_m']+roots[:,None]
            np.testing.assert_allclose(decoded,native,atol=5.1e-5,rtol=0)
            actual=(decoded[:,slot_vertices]*bary[None,:,:,None]).sum(axis=2)
            expected_slots=(native[:,slot_vertices]*bary[None,:,:,None]).sum(axis=2)
            np.testing.assert_allclose(actual,expected_slots,atol=5.1e-5,rtol=0)

    def test_human_export_refuses_directory_fallback_and_changed_model_hash(self):
        import copy
        import tempfile
        sys.path.insert(0,'/data/workspace/motion_studio/externals/UMR/scripts')
        import smpl_surface_retarget_common as common
        import retarget_smpl_to_humanoid_surface_vector as robot
        from motion_studio.integrations._umr_studio_human import export_human_motion
        config=json.loads((self.native/'humanoid_retarget_runtime_config.json').read_text())
        receipts=json.loads((self.bundle/'receipts.json').read_text())
        sample=next((self.bundle/'native/sampling').rglob('dataset.npz'))
        binding_file=next((self.bundle/'native/binding').rglob('binding.npz'))
        with np.load(binding_file,allow_pickle=False) as saved:
            binding={'face_ids':saved['source_face_ids'],'bary':saved['source_bary']}
        for directory_fallback in (True,False):
            with self.subTest(directory_fallback=directory_fallback), tempfile.TemporaryDirectory() as tmp:
                supplied=copy.deepcopy(config);expected=copy.deepcopy(self.receipt['inputs'])
                if directory_fallback:
                    supplied['smplx_model_dir']=str(Path(supplied['smplx_model_dir']).parent)
                else:
                    expected['motion']['model_sha256']='0'*64
                with self.assertRaisesRegex(ValueError,'exact validated|model changed'):
                    export_human_motion(self.native,Path(tmp),supplied,binding,common,robot,np,
                                        dataset_path=sample,expected_motion=expected)
                self.assertEqual(list(Path(tmp).iterdir()),[])
