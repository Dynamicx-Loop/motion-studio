"""Independent worked-example checks, including symmetry and fixed boundaries."""
import unittest
import numpy as np
from calibration import LandmarkCalibration,calibrate_slots,infer_calibration
class CalibrationTests(unittest.TestCase):
    def test_worked_example(self):
        p=np.array([[-5.,1,2],[-3.,1,2],[-2.,1,2],[-1.5,1,2],[0.,1,2],[1.5,1,2],[2.,1,2],[3.,1,2],[5.,1,2]])
        before=p.copy();cs=[LandmarkCalibration(s,1,2,3,4,1,[],[]) for s in [-1,1]]
        q=calibrate_slots(p,cs)
        np.testing.assert_allclose(q[:,0],[-5,-3.5,-3,-2,0,2,3,3.5,5]);np.testing.assert_array_equal(p,before);np.testing.assert_array_equal(q[:,1:],p[:,1:]);self.assertTrue(np.all(np.diff(q[:,0])>0))
    def test_landmark_inference_and_invalid_order(self):
        p=np.array([[1.,0,0],[2.,0,0],[4.,0,0]])
        c=infer_calibration(p,p,p[0],p[1],1,3,4,1);self.assertEqual(c.wrist_slot_ids,[1])
        with self.assertRaises(ValueError):infer_calibration(p,p,p[1],p[0],1,3,4,1)
        with self.assertRaises(ValueError):calibrate_slots(p,[c,c])
if __name__=='__main__':unittest.main()
