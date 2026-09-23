from make_3d_train_data.yolo_writer import yolo_line,write_yolo
def test_mapping(): assert yolo_line(1,[0,0,100,50],100,50).split()[0]=="0"
def test_last_mapping(tmp_path):
    p=tmp_path/"x.txt"; write_yolo(p,[{"canonical_id":37,"bbox_xyxy":[0,0,10,10]}],20,20); assert p.read_text().startswith("36 ")

