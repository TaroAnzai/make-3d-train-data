from make_3d_train_data.class_defs import CLASSES,BY_ID,BY_NAME
def test_canonical_classes():
    assert len(CLASSES)==37 and len(BY_ID)==37 and len(BY_NAME)==37
    assert BY_ID[1].name=="1m" and BY_ID[37].name=="red5s" and BY_NAME["east"].canonical_id==28

