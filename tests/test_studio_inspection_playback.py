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
