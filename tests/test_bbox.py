from make_3d_train_data.bbox import BBox,clip_bbox,bbox_from_points
def test_clip(): assert clip_bbox([-5,10,120,90],100,80).xyxy()==[0.,10.,100.,80.]
def test_outside(): assert clip_bbox([110,0,120,10],100,100) is None
def test_points(): assert bbox_from_points([(1,2),(5,8)],10,10).xywh()==[1,2,4,6]

