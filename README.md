# Nishikie IIIF Metadata Repository

このリポジトリは、nishikie-iiif-images S3バケットに格納された画像のメタデータを管理します。

## ディレクトリ構造

```
nishikie-metadata/
├── _system/
│   └── next_id.txt          # 次に使用可能なマニフェストID
├── manifests/
│   ├── 1.json              # マニフェストID 1のメタデータ
│   ├── 2.json              # マニフェストID 2のメタデータ
│   └── 3.json              # マニフェストID 3のメタデータ
└── README.md
```

## S3バケット構造

```
s3://nishikie-iiif-images/
├── 1/
│   └── 0001.tif
├── 2/
│   └── 0001.tif
└── 3/
    ├── 0001.tif
    └── 0002.tif
```

## 新しい画像を追加するワークフロー

### 1. 次のIDを確認

```bash
cat _system/next_id.txt
# 出力例: 4
```

### 2. S3に画像をアップロード

```bash
# マニフェストID 4、画像1枚の場合
aws s3 cp image.tif s3://nishikie-iiif-images/4/0001.tif --region ap-northeast-1

# 複数画像の場合
aws s3 cp image1.tif s3://nishikie-iiif-images/4/0001.tif --region ap-northeast-1
aws s3 cp image2.tif s3://nishikie-iiif-images/4/0002.tif --region ap-northeast-1
```

### 3. メタデータファイルを作成

```bash
# manifests/4.json を作成
cat > manifests/4.json << 'EOF'
{
  "manifest_id": "4",
  "title": "作品タイトル",
  "title_en": "Title in English",
  "type": "manuscript",
  "format": "single|diptych|orihon",
  "source": "adeac",
  "source_url": "https://...",
  "date_created": "2025-11-18",
  "original_filename_prefix": "...",
  "canvases": [
    {
      "id": "0001",
      "label": "Page 1",
      "s3_path": "4/0001.tif",
      "original_filename": "original.tif",
      "width": null,
      "height": null,
      "format": "image/tiff"
    }
  ],
  "metadata": {
    "attribution": "Source: ADEAC",
    "license": null,
    "description": "..."
  }
}
EOF
```

### 4. 次のIDを更新

```bash
echo "5" > _system/next_id.txt
```

### 5. コミット＆プッシュ

```bash
git add .
git commit -m "Add manifest 4"
git push origin main
```

## IIIF画像サーバーURL

```
https://onmw6bcpc6cnfluolfvlzpqr6y0qaarr.lambda-url.ap-northeast-1.on.aws/iiif/3/{manifest_id}%2F{image_id}/info.json
```

例:
- `https://.../iiif/3/1%2F0001/info.json` - マニフェスト1、画像0001
- `https://.../iiif/3/3%2F0001/info.json` - マニフェスト3、画像0001
- `https://.../iiif/3/3%2F0002/info.json` - マニフェスト3、画像0002

## メタデータスキーマ

各マニフェストJSONファイルには以下のフィールドが含まれます:

- `manifest_id`: マニフェストID（数字の文字列）
- `title`: 日本語タイトル
- `title_en`: 英語タイトル
- `type`: 種類（manuscript, print, etc.）
- `format`: 形式（single, diptych, orihon, etc.）
- `source`: データソース
- `source_url`: ソースURL
- `date_created`: メタデータ作成日
- `original_filename_prefix`: 元のファイル名プレフィックス
- `canvases`: 画像配列
  - `id`: 画像ID（0001, 0002, ...）
  - `label`: 表示ラベル
  - `s3_path`: S3パス
  - `original_filename`: 元のファイル名
  - `width`: 幅（ピクセル）
  - `height`: 高さ（ピクセル）
  - `format`: MIMEタイプ
- `metadata`: 追加メタデータ
  - `attribution`: 帰属表示
  - `license`: ライセンス
  - `description`: 説明

## ライセンス

TBD
