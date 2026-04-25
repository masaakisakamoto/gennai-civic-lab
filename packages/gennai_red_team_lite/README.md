# gennai-red-team-lite

源内互換AIアプリに対する軽量な安全性smoke testです。

v0.4では、以下のような最低限のリスクを自動確認します。

- プロンプトインジェクションを「指示」として扱わない
- 個人情報らしき文字列をsafe modeでマスクする
- 根拠がない質問に断定回答しない

```bash
make red-team
```
