# ボス用 UEFN スクリプト(boss_import.py / boss_make_assets.py / boss_import_anims.py)の共通設定。
# 新しいボスを作るときは、ここの4行(PROJECT / ASSETS_ROOT / BOSS / PREFIX)だけ書き換える。
import os

# UEFN プロジェクトのコンテンツのルート(コンテンツブラウザで一番上に見えるプロジェクト名)
PROJECT = "MyProject"
# 作業フォルダ(Tripo の FBX や Blender の出力を置く場所)
ASSETS_ROOT = "D:/BossWork"
BOSS = "NewBoss"     # ボス名(英数字)。アセット名とフォルダ名に使う
PREFIX = "NB"        # アニメのアセット名の頭 (例: NB_Idle)

# Blender で大きさを焼き込んだ FBX(anims_ue)の場所
SRC_DIR = ASSETS_ROOT + "/" + BOSS + "/anims_ue"
# メッシュを取り出す FBX(どのアニメの FBX にもメッシュは入っている)
MESH_FBX = "Idle.fbx"

FOLDER = "/" + PROJECT + "/Boss/" + BOSS
MESH_NAME = "SK_" + BOSS
AP_NAME = "AP_" + BOSS
BP_NAME = "BP_" + BOSS


def anim_name(fbx):
    return PREFIX + "_" + os.path.splitext(os.path.basename(fbx))[0]
