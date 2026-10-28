# uefn-boss-kit

Scripts for turning an AI-generated, auto-rigged character (UE5 Mannequin skeleton) into a walking, attacking boss NPC in UEFN (Unreal Editor for Fortnite).

AI で作ったキャラクター(UE5 マネキンの骨でリグ済み)を、UEFN で歩いて近づき攻撃してくるボス NPC にするためのスクリプト集です。

## 中身

### Blender(5.0 以上・コマンドで実行)
`blender -b --factory-startup -P <スクリプト> -- <引数>`

| スクリプト | 内容 |
|---|---|
| `tools/blender_fix_tripo_fbx.py` | FBX の大きさ(root 骨の倍率)をメッシュ・骨・移動キーに焼き込み、cm 単位で倍率のない FBX にする |
| `tools/blender_make_loop.py` | 待機・歩きを指定コマで切り、つなぎ目をなめらかにしてループさせる |
| `tools/blender_retarget_motion.py` | Mixamo / UE5 Manny / Mesh2Motion(GLB)/ Kimodo(BVH)のアニメをボスの骨に移し替える |
| `tools/blender_add_lunge.py` | 攻撃アニメに前への踏み込みを足す(軸足は固定、脚は 2 ボーン IK で曲げ直す) |
| `tools/blender_retime_attack.py` | 攻撃の振り下ろしを速め、溜めと止めを入れる |
| `tools/blender_measure_attack.py` | 攻撃アニメから当たる時刻・長さ・届く距離を測る |

各スクリプトの引数は、ファイル先頭のコメントに書いてあります。

### UEFN(Python・コンソールの `py` コマンドで実行)
| スクリプト | 内容 |
|---|---|
| `tools/boss_config.py` | 共通設定(プロジェクト名・作業フォルダ・ボス名・アニメ名の頭) |
| `tools/boss_import.py` | メッシュ・スケルトン・アニメを取り込む(倍率 1) |
| `tools/boss_make_assets.py` | アニメーションプリセット(AnimPreset_BipedLocomotion の子)と見た目の Blueprint を作る |
| `tools/boss_import_anims.py` | アニメを追加で取り込む |

### Verse
| ファイル | 内容 |
|---|---|
| `verse/simple_boss_behavior.verse` | プレイヤーを見つけて歩いて近づき、攻撃の一覧からランダムに選んで攻撃する `npc_behavior`。待機・歩きはアニメーションプリセットに任せる |

## 動作確認した環境
- Blender 5.2
- UEFN(2026年10月時点)

## ライセンス
MIT License(`LICENSE` を参照)。
アニメーションやモデルなどの素材は含みません。移し替えに使う素材は、それぞれのライセンスに従ってください。
