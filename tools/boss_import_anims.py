# boss_config.py のボスに、後から作ったアニメを追加で取り込む(同じ名前は上書き)。メッシュは取り込まない。
# 取り込むファイルは FILES に anims_ue のファイル名で並べる。アセット名は <PREFIX>_<ファイル名>。
import os
import sys
import importlib
import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss_config as C
importlib.reload(C)

FILES = [  # 追加で取り込むファイル名(anims_ue の中)
]

def log(msg):
    unreal.log_warning("BOSS_ANIM " + msg)

skeleton = unreal.load_asset(C.FOLDER + "/" + C.MESH_NAME + "_Skeleton")
if not skeleton:
    raise RuntimeError("スケルトンがない: " + C.FOLDER + "/" + C.MESH_NAME + "_Skeleton(先に boss_import.py)")
tasks = []
for f in FILES:
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", False)
    ui.set_editor_property("import_animations", True)
    ui.set_editor_property("import_as_skeletal", True)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("skeleton", skeleton)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", C.SRC_DIR + "/" + f)
    task.set_editor_property("destination_path", C.FOLDER)
    task.set_editor_property("destination_name", C.anim_name(f))
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", ui)
    tasks.append(task)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

# 確認: root 骨の倍率が 1、腰の高さが基準ポーズと同程度なら正しい
for f, task in zip(FILES, tasks):
    name = C.anim_name(f)
    log("取り込み: " + ", ".join(task.get_editor_property("imported_object_paths")))
    anim = unreal.load_asset(C.FOLDER + "/" + name)
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, 0.0, unreal.AnimPoseEvaluationOptions())
    for b in ("root", "pelvis"):
        t = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.LOCAL)
        log("%s %s z=%.1f scale=%.3f 長さ=%.2f秒" % (name, b, t.translation.z, t.scale3d.x, anim.get_editor_property("sequence_length")))
