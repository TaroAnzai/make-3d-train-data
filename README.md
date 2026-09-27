# make-3d-train-data

Blender と Python で、麻雀牌認識 AI 用の合成画像・BBox アノテーションを自動生成する独立プロジェクトです。37 種類の牌、fixed/random 配置、難条件、COCO、YOLO、再現可能な seed を扱います。既存の `mahjong-tile-ai` を import・変更せず、生成物を後から同プロジェクトの `data/incoming/` 等へ渡す想定です。

プロジェクトルートは `~/development/make-3d-train-data/` です。

## セットアップ

```bash
cd ~/development/make-3d-train-data
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

`bpy` は pip 依存に含めません。推奨は Blender 5.2 LTS 以降の公式 Linux x64 バイナリです。公式tarballをユーザー領域（例: `~/software/blender-5.2.x/`）へ展開し、`~/.local/bin/blender` からリンクするとsudoなしで利用できます。OSパッケージやSnapも利用可能ですが、古い版ではEEVEE識別子が異なる場合があります。

Blender がなくても、設定検証、シーン preview、BBox/annotation ロジックの pytest を実行できます。画像生成には Blender と、リポジトリ内の `assets/blender/tiles_master.blend`・`assets/masters/table_assets.blend` が必要です。

## CLI

```bash
python -m make_3d_train_data doctor
python -m make_3d_train_data doctor --blender-bin /path/to/blender
python -m make_3d_train_data config validate configs/default.yaml
python -m make_3d_train_data scene preview --config configs/default.yaml --count 3
python -m make_3d_train_data generate --config configs/fixed_sample.yaml
python -m make_3d_train_data generate --config configs/reference_table.yaml
python -m make_3d_train_data generate --config configs/default_one.yaml
python -m make_3d_train_data generate --config configs/default.yaml --count 10
python -m make_3d_train_data generate --config configs/default_random.yaml
```

Blender の探索順は `--blender-bin`、`BLENDER_BIN`、YAML の `blender.binary`、`PATH` 上の `blender` です。未検出時の `generate` は traceback ではなく対処方法を含むエラーを返します。
`generate --count` で生成枚数を指定すると、YAML の `output.count` より優先されます。省略時は YAML の値を使用します。
`generate` の実行中は、画像の処理が完了するたびに進むプログレスバーを表示します。

```bash
command -v blender
blender --version
blender --background --factory-startup --python-expr "import bpy; print('BLENDER_OK', bpy.app.version_string)"
export BLENDER_BIN=/path/to/blender  # PATHにない場合だけ
python -m make_3d_train_data doctor
```

Blender 5.2.2 LTSではEEVEEのengine IDは `BLENDER_EEVEE` です。レンダラは利用可能engineを実行時検証し、旧設定の `BLENDER_EEVEE_NEXT` も対応可能な場合は変換します。

`generate` は YAML の `assets.tile_blend` と `assets.mat_blend` を読み込みます。`configs/` 内の YAML はすべて同じ master を参照します。パスはプロジェクトルートで実行したときの相対パスです。別の場所から実行する場合は絶対パスを指定してください。各画像のレンダリング時に master を読み込みます。

## 設定とシーン

設定は YAML です。`scene preview` は `general.seed + 画像 index` を使うため、同じ設定から同じ `SceneDescription` が得られます。`generate` は設定の seed、出力フォルダーの連番、画像ごとの試行番号を組み合わせて seed を作ります。同じ設定で再実行しても異なる画像を生成し、出力先にある既存データセットと JPEG 内容が重複した場合は再描画します。牌の座標、カメラ距離、マットの寸法はメートル単位です。マットは690 mm四方、牌の標準寸法は約20 × 28 × 16.5 mmです。`z: 0` はフェルト面に接地する高さで、回転させた牌も最も低い点をフェルト面に合わせます。

- `fixed`: `tiles_fixed` の class、3D 位置、回転、scale をそのまま使用します。
- `random`: 牌種/枚数/XYZ/回転/scale/密集/重なり/端切れ/小牌、カメラ距離・tilt/yaw/roll、照明を乱数化します。
- `noise`: Blender 描画後に brightness、contrast、Gaussian blur、JPEG quality を乱数化します。
- `configs/hard_cases.yaml`: 小牌、密集、重なり、斜め視点、端切れ、暗所、blur を強化しています。
- `configs/fixed_sample.yaml`: 3枚の牌を固定配置する1枚確認用シーンです。
- `configs/reference_table.yaml`: master マット上に、手前の立てた手牌、橙色の伏せ牌壁、中央と奥の捨て牌を固定配置する1枚確認用シーンです。
- `configs/default.yaml`: 写真を基準にした変化付きシーンです。手牌は13/14枚を交互に生成し、画像ごとに立てた手牌と表向きに寝かせた手牌を選びます。37牌種の出現回数を全画像でほぼ均等にします。撮影条件と背景は `variations` の確率・範囲で変化します。背景の牌は描画されますが、COCO/YOLO のラベルには手牌だけを含めます。
- `configs/default_random.yaml`: 以前の `default.yaml` のランダム配置設定です。変更前の内容をそのまま残しています。
- `configs/default_one.yaml`: `default_random.yaml` と同じランダム配置・描画条件で1枚生成します。

### 写真ベース設定のランダム化項目

`configs/default.yaml` の各画像では、手牌の牌種・枚数・向き・位置・間隔・回転、カメラ距離と傾きを変えます。カメラの yaw・roll・注視点、明るさ・コントラストは各項目80%の確率で、JPEG品質・捨て牌・牌山は各項目50%の確率で変えます。ぼかしは約13.5%の画像に適用されます。

牌の `roughness` と `specular`、照明の光源位置・強度・色温度（4000〜6200 K）、フェルトの緑系の色・明るさ・粗さ・微細なムラは**毎画像**変えます。反射と色の範囲は牌の模様を読み取れる室内撮影を想定しています。手牌の1枚の端にかかる小さな指先は約1%の画像にのみ追加します。これらの値と遮蔽の有無は manifest に記録します。

`scene preview` は Blender を起動せず、通常 Python が作る JSON を表示します。実レンダリング時も一時 JSON を Blender に渡し、Blender が画像と投影結果 JSON を返します。通常コードは `bpy` を import しません。

背景ディレクトリに JPG/PNG がある場合、選択したパスを manifest に記録できます。描画面は master のマットで、外側には暗い卓面を置きます。背景画像と `scene.background.color` の描画には未対応です。

## 牌と canonical 37

ID は固定です: `1..9 = 1m..9m`、`10..18 = 1p..9p`、`19..27 = 1s..9s`、`28..31 = east/south/west/north`、`32..34 = white/green/red`、`35..37 = red5m/red5p/red5s`。

定義元は `class_defs.py` の一か所です。COCO category ID は canonical ID をそのまま使います。YOLO は 0-based のため `YOLO ID = canonical ID - 1`（canonical 1 → YOLO 0、canonical 37 → YOLO 36）です。`classes.json` に対応も保存します。

牌は `assets/blender/tiles_master.blend` の `master_tile` を複製し、共有メッシュとパック済みの37種の牌面画像を使います。字牌の英語名と master のコード（例: `east` → `ton`、`red5p` → `5pr`）はレンダラが変換します。マットは `assets/masters/table_assets.blend` の `mat_table` を使います。牌面の元絵は `external/riichi-mahjong-tiles` サブモジュールにあり、ライセンスは同ディレクトリの `LICENSE.md` を参照してください。既存の `textures generate` コマンドは元絵のコピーを作りますが、`generate` では使用しません。

## 出力

```text
~/3d-train-data/default-01-500/
├── dataset.yaml
├── images/000001.jpg
├── annotations/
│   ├── instances.json
│   └── yolo/000001.txt
└── meta/
    ├── manifest.jsonl
    ├── generation_summary.json
    ├── classes.json
    └── used_config.yaml
```

フォルダー名は `<設定ファイル名>-<連番>-<生成枚数>` です。連番は同じ設定ファイル名の既存データセットから最大値を調べて決めます。出力先は YAML の `output.root` で変更できます。`dataset.yaml` には `name: cg_YYYYMMDD_NNN`、`format: coco`、`class_schema: canonical37` を記録します。COCO は必ず出力し、YOLO は `output.formats` に `yolo` がある場合に出力します。

COCO は全 37 categories と、画像ごとの pixel `xywh`、area を保存します。YOLO は正規化 `cx cy width height` を保存します。manifest は画像、seed、サイズ、mode、牌 class/canonical ID、`bbox_xyxy`/`bbox_xywh`、3D 位置、回転、scale、カメラ、照明、背景を 1 画像 1 行で保存します。

## BBox と既知の制約

v1 は各 3D 牌の 8 bounding-box corner をカメラへ投影し、最終画像境界に clip します。完全画面外または幅/高さ 0 以下は除外します。pixel-level 可視領域ではないため、重なった牌の BBox は遮蔽部分を含み、`occluded` は現状 `false` です。object-index pass / segmentation mask を追加し、visible-pixel BBox、遮蔽率、instance mask を算出するのが次の改善点です。

ほかの制約として、背景画像そのものの Blender 合成、物理衝突による自然な積み重なり、motion blur、複数の牌モデル、完全なフォトリアル性は未対応です。被写界深度は YAML で設定できます。現状の overlap は位置クラスタリングと Z 乱数による近似です。

## テスト

```bash
pytest
pytest -m blender
```

Blender smoke test は Blender 未導入なら明示的に skip します。導入済みなら fixed 1 枚を headless 生成し、画像と COCO を確認します。今後は random 数枚の統合テスト、segmentation の精度テスト、実画像との domain-gap 評価を追加してください。
