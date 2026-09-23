import json
from make_3d_train_data.manifest_writer import ManifestWriter
def test_manifest(tmp_path):
    p=tmp_path/"m.jsonl"; w=ManifestWriter(p); w.append({"image":"a.jpg"}); w.append({"image":"b.jpg"}); assert len(p.read_text().splitlines())==2

