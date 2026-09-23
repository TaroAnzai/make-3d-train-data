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

Blender がなくても、設定検証、シーン preview、37 テクスチャ生成、BBox/annotation ロジックの pytest を実行できます。導入後はコード変更なしで headless レンダリングを利用できます。

## CLI

```bash
python -m make_3d_train_data doctor
python -m make_3d_train_data doctor --blender-bin /path/to/blender
python -m make_3d_train_data textures generate
python -m make_3d_train_data config validate configs/default.yaml
python -m make_3d_train_data scene preview --config configs/default.yaml --count 3
python -m make_3d_train_data generate --config configs/fixed_sample.yaml
python -m make_3d_train_data generate --config configs/reference_table.yaml
python -m make_3d_train_data generate --config configs/default.yaml
```

Blender の探索順は `--blender-bin`、`BLENDER_BIN`、YAML の `blender.binary`、`PATH` 上の `blender` です。未検出時の `generate` は traceback ではなく対処方法を含むエラーを返します。

```bash
command -v blender
blender --version
blender --background --factory-startup --python-expr "import bpy; print('BLENDER_OK', bpy.app.version_string)"
export BLENDER_BIN=/path/to/blender  # PATHにない場合だけ
python -m make_3d_train_data doctor
```

Blender 5.2.2 LTSではEEVEEのengine IDは `BLENDER_EEVEE` です。レンダラは利用可能engineを実行時検証し、旧設定の `BLENDER_EEVEE_NEXT` も対応可能な場合は変換します。

## 設定とシーン

設定は YAML です。`general.seed + 画像 index` が各シーンの seed なので、同じ設定から同じ `SceneDescription` が得られます。

- `fixed`: `tiles_fixed` の class、3D 位置、回転、scale をそのまま使用します。
- `random`: 牌種/枚数/XYZ/回転/scale/密集/重なり/端切れ/小牌、カメラ距離・tilt/yaw/roll、照明、背景色を乱数化します。
- `noise`: Blender 描画後に brightness、contrast、Gaussian blur、JPEG quality を乱数化します。
- `configs/hard_cases.yaml`: 小牌、密集、重なり、斜め視点、端切れ、暗所、blur を強化しています。
- `configs/reference_table.yaml`: 緑の麻雀卓、手前の立てた手牌、橙色の伏せ牌壁、中央と奥の捨て牌、被写界深度を持つ実卓写真風の1枚確認用シーンです。

`scene preview` は Blender を起動せず、通常 Python が作る JSON を表示します。実レンダリング時も一時 JSON を Blender に渡し、Blender が画像と投影結果 JSON を返します。通常コードは `bpy` を import しません。

背景ディレクトリに JPG/PNG がある場合、選択したパスを manifest に記録します。v1 の Blender 床面はランダム色であり、背景画像の平面マッピングは未対応です。

## 牌と canonical 37

ID は固定です: `1..9 = 1m..9m`、`10..18 = 1p..9p`、`19..27 = 1s..9s`、`28..31 = east/south/west/north`、`32..34 = white/green/red`、`35..37 = red5m/red5p/red5s`。

定義元は `class_defs.py` の一か所です。COCO category ID は canonical ID をそのまま使います。YOLO は 0-based のため `YOLO ID = canonical ID - 1`（canonical 1 → YOLO 0、canonical 37 → YOLO 36）です。`classes.json` に対応も保存します。

牌面は外部の市販デザインに依存せず自動生成します。萬子は数と萬、筒子は円、索子は竹、字牌は漢字風の図案、赤5は赤い図案です。Blender 側は厚みのある面取り済み直方体を作成し、素材とテクスチャを適用します。事前作成 `.blend` は不要です。

## 出力

```text
output/<dataset_name>/
├── images/000001.jpg
├── labels/
│   ├── instances.json
│   └── yolo/000001.txt
└── meta/
    ├── manifest.jsonl
    ├── generation_summary.json
    ├── classes.json
    └── used_config.yaml
```

COCO は全 37 categories と、画像ごとの pixel `xywh`、area を保存します。YOLO は正規化 `cx cy width height` を保存します。manifest は画像、seed、サイズ、mode、牌 class/canonical ID、`bbox_xyxy`/`bbox_xywh`、3D 位置、回転、scale、カメラ、照明、背景を 1 画像 1 行で保存します。

## BBox と既知の制約

v1 は各 3D 牌の 8 bounding-box corner をカメラへ投影し、最終画像境界に clip します。完全画面外または幅/高さ 0 以下は除外します。pixel-level 可視領域ではないため、重なった牌の BBox は遮蔽部分を含み、`occluded` は現状 `false` です。object-index pass / segmentation mask を追加し、visible-pixel BBox、遮蔽率、instance mask を算出するのが次の改善点です。

ほかの制約として、背景画像そのものの Blender 合成、物理衝突による自然な積み重なり、motion/depth-of-field blur、複数の牌モデル・材質、完全なフォトリアル性は未対応です。現状の overlap は位置クラスタリングと Z 乱数による近似です。

## テスト

```bash
pytest
pytest -m blender
```

Blender smoke test は Blender 未導入なら明示的に skip します。導入済みなら fixed 1 枚を headless 生成し、画像と COCO を確認します。今後は random 数枚の統合テスト、segmentation の精度テスト、実画像との domain-gap 評価を追加してください。
