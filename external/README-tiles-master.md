# 共通麻雀牌アセット

`assets/blender/tiles_master.blend` は、既存の `assets/masters/master_tile.blend` の寸法と本体形状を使った共通牌です。`final_master_tile.blend` がある場合はそちらを優先します。シーン内のメッシュオブジェクトは `master_tile` の 1 個で、材質スロットは `tile_body_white`、`tile_back_orange`、`tile_face` の順です。牌面の物理形状はどの牌種でも同じです。

37 枚の PNG は `assets/textures/tiles/` に保存し、`.blend` 内にも `1m` などの名前の画像データとしてパックしています。ファイル名は `1m.png`～`9m.png`、`1p.png`～`9p.png`、`1s.png`～`9s.png`、`ton.png`、`nan.png`、`sha.png`、`pei.png`、`haku.png`、`hatsu.png`、`chun.png`、`5mr.png`、`5pr.png`、`5sr.png` です。元絵は `external/riichi-mahjong-tiles/Export/Regular/` にあり、ライセンスは同サブモジュールの `LICENSE.md` を参照してください。

Blender Python では `external/tile_asset.py` の `set_tile_type(obj, code)` を使います。`master_tile` を複製してこの関数へ `"1m"`、`"6p"`、`"hatsu"`、`"5sr"` などを渡すと、そのオブジェクト専用の牌面マテリアルを割り当て、パック済み画像に切り替えます。複製間でメッシュは共有できます。ひな型の `master_tile` は `1m` です。

再生成: `blender -b --python external/build_tiles_master.py -- --project-root .`
