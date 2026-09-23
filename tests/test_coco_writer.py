from make_3d_train_data.coco_writer import CocoWriter
def test_coco(tmp_path):
    w=CocoWriter(); w.add_image(1,"x.jpg",100,100,[{"canonical_id":37,"bbox_xywh":[1,2,3,4]}]); w.write(tmp_path/"x.json")
    assert len(w.data()["categories"])==37 and w.data()["annotations"][0]["area"]==12

