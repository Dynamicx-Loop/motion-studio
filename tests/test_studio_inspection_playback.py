"""Independent rigid replay worked examples applied to the new owned exporter."""
CHECK_TIER = 'robot-static'
CHECK_MODULES = ('numpy','mujoco')
import test_umr_binding_playback_runtime as reference
from motion_studio.integrations._umr_studio_motion import export_motion


class StudioBindingPlaybackTests(reference.BindingPlaybackTests):
    def export(self):
        import numpy as np
        import mujoco
        return export_motion(self.run,self.run,self.model,self.binding,self.robot,mujoco,np)

    def test_human_quantization_reference_on_both_sides_of_64_frame_boundary(self):
        import numpy as np
        from motion_studio.integrations._umr_studio_human import encode_root_relative
        roots=np.array([[20.+frame,5.,-10.] for frame in range(65)])
        local=np.broadcast_to(np.array([[[.100049,-.300051,.00001],[1.,0.,-1.]]]),(65,2,3))
        native=local+roots[:,None]
        encoded=encode_root_relative(native,roots,np)
        for frame in (0,63,64):
            np.testing.assert_array_equal(encoded[frame],[[1000,-3001,0],[10000,0,-10000]])
        decoded=encoded.astype(float)*.0001+roots[:,None]
        np.testing.assert_allclose(decoded,native,atol=5.1e-5,rtol=0)

    def test_shifted_root_preserves_decoded_binding_precision(self):
        import numpy as np
        self.qpos[:, :3] += [100.123456, 50.123456, 0.]
        self.save()
        meta = self.export()
        matrices = np.fromfile(self.run / meta['transforms'], dtype=meta.get('transform_dtype', '<f4')).reshape(3, 2, 3, 4)
        points = np.einsum('fgij,gj->fgi', matrices[:, :, :, :3], self.binding['local_pos']) + matrices[:, :, :, 3]
        expected = np.array([[[0, 1, 0], [0, 1, 2]], [[3, 1, 2], [4, 1, 1]], [[-2, 2, -1], [-3, 2, 0]]], dtype=float)
        expected += [50.123456, 0., 100.123456]
        np.testing.assert_allclose(points, expected, atol=5e-7, rtol=0)
        self.assertLessEqual(meta['max_binding_axis_error_m'], 5e-7)
        self.assertEqual(meta['transform_schema'], 2)
        self.assertEqual(meta['transform_dtype'], '<f8')
