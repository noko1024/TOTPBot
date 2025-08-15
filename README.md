# TOTPBot

Discord用のTOTP（Time-based One-Time Password）管理ボットです。サーバーごとにTOTPトークンを設定し、認証されたユーザーがワンタイムパスワードを生成できます。

## 機能

- 🔐 サーバーごとのTOTPトークン管理
- 👥 ロールベースのアクセス制御
- 📜 TOTP生成履歴の記録
- 🛡️ サーバー管理者による自律的な設定管理

## コマンド一覧

### 一般ユーザー向け
- `/totp` - 6桁のワンタイムパスワードを生成
- `/show [log_limit]` - TOTP生成履歴を表示（デフォルト: 10件）

### 管理者向け
- `/set_token <token> [guild_id]` - TOTPトークンを設定
- `/delete_token` - TOTPトークンを削除
- `/set_role <role>` - TOTP生成を許可するロールを設定
- `/delete_role <role> [guild_id]` - 認証ロールを削除

### BOTオーナー限定
- `/shutdown` - ボットをシャットダウン

## セットアップ

### 前提条件

- Docker及びDocker Composeがインストールされていること
- Discordボットトークンを取得済みであること

### 手順

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/TOTPBot.git
cd TOTPBot
```

2. 環境変数を設定
```bash
cp .env.template .env
```

`.env`ファイルを編集し、以下の値を設定：
- `BOT_TOKEN`: DiscordボットのトークンDiscordボットトークン
- `OWNER_ID`: ボットオーナーのDiscordユーザーID

3. Dockerコンテナを起動
```bash
docker compose up -d
```

4. ログを確認
```bash
docker compose logs -f
```

## 初回設定

1. ボットをDiscordサーバーに招待
2. サーバー管理者またはBOTオーナーが `/set_token` コマンドでTOTPトークンを設定
3. 必要に応じて `/set_role` コマンドで特定のロールにのみTOTP生成を許可

## 権限システム

### TOTPトークン・ロール管理権限
- **自分のサーバー**: BOTオーナーまたはサーバー管理者
- **他のサーバー**: BOTオーナーのみ

### TOTP生成権限
- 認証ロールが設定されていない場合: 全員
- 認証ロールが設定されている場合: 指定されたロールを持つユーザーのみ

## データベース

SQLite（`TOTPlog.db`）を使用してデータを保存：
- サーバー情報
- TOTPトークン（暗号化推奨）
- 認証ロール設定
- TOTP生成ログ

### マイグレーション

Alembicを使用してデータベーススキーマを管理：

```bash
# コンテナ内でマイグレーションを実行
docker compose exec totpbot alembic upgrade head
```

## 開発

### ローカル環境での実行

1. Python仮想環境を作成
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. データベースを初期化
```bash
alembic upgrade head
```

4. ボットを起動
```bash
python main.py
```

### 新しいマイグレーションの作成

```bash
alembic revision --autogenerate -m "説明"
```

## トラブルシューティング

### ボットが起動しない
- `.env`ファイルの`BOT_TOKEN`と`OWNER_ID`が正しく設定されているか確認
- Dockerログを確認: `docker compose logs totpbot`

### 権限エラー
- ボットに必要な権限があるか確認（メッセージ送信、スラッシュコマンド使用）
- サーバー管理者権限を持っているか確認

### データベースエラー
- `TOTPlog.db`ファイルの権限を確認
- マイグレーションが実行されているか確認

## セキュリティに関する注意

- TOTPトークンは機密情報です。本番環境では暗号化することを推奨します
- `.env`ファイルは絶対にGitにコミットしないでください
- 定期的にTOTP生成ログを確認し、不審なアクセスがないか監視してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。