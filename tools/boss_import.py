# boss_config.py のボスのメッシュ・スケルトン・物理アセットと、anims_ue にある全アニメを取り込む。
# FBX は Blender で大きさを焼き込み済み(cm 単位・倍率なし)なので、取り込みの倍率は 1 のまま。
# 別のボスを上書きしないよう、同じ名前のメッシュが既にあれば止める(作り直すときは消してから実行)。
import os
import sys
import importlib
import unreal

# UEFN は一度読んだモジュールを覚えているので、設定を書き換えても反映されるよう読み直す
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss_config as C
importlib.reload(C)

def log(msg):
    unreal.log_warning("BOSS_IMPORT " + msg)

tools = unreal.AssetToolsHelpers.get_asset_tools()
lib = unreal.EditorAssetLibrary

mesh_path = C.FOLDER + "/" + C.MESH_NAME
if lib.does_asset_exist(mesh_path):
    raise RuntimeError("既にある: " + mesh_path + "(boss_config.py の BOSS を確認)")
if not os.path.isfile(C.SRC_DIR + "/" + C.MESH_FBX):
    raise RuntimeError("FBX がない: " + C.SRC_DIR + "/" + C.MESH_FBX)

def run_task(filename, name, ui):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", filename)
    task.set_editor_property("destination_path", C.FOLDER)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", ui)
    tools.import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths"))

ui = unreal.FbxImportUI()
ui.set_editor_property("import_mesh", True)
ui.set_editor_property("import_as_skeletal", True)
ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
ui.set_editor_property("import_materials", True)
ui.set_editor_property("import_textures", True)
ui.set_editor_property("import_animations", False)
ui.set_editor_property("create_physics_asset", True)
log("メッシュ: " + ", ".join(run_task(C.SRC_DIR + "/" + C.MESH_FBX, C.MESH_NAME, ui)))

mesh = unreal.load_asset(mesh_path)
skeleton = mesh.get_editor_property("skeleton")

anims = []
for f in sorted(x for x in os.listdir(C.SRC_DIR) if x.lower().endswith(".fbx")):
    name = C.anim_name(f)
    aui = unreal.FbxImportUI()
    aui.set_editor_property("import_mesh", False)
    aui.set_editor_property("import_animations", True)
    aui.set_editor_property("import_as_skeletal", True)
    aui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    aui.set_editor_property("import_materials", False)
    aui.set_editor_property("import_textures", False)
    aui.set_editor_property("skeleton", skeleton)
    log("アニメ: " + ", ".join(run_task(C.SRC_DIR + "/" + f, name, aui)))
    anims.append(name)

# 確認: root 骨の倍率が 1、腰の高さが体の大きさに見合っていれば正しい
def fmt(t):
    return "z=%.1f scale=%.3f" % (t.translation.z, t.scale3d.x)
ref = unreal.AnimPoseExtensions.get_reference_pose(skeleton)
for b in ("root", "pelvis"):
    log("基準ポーズ %s %s" % (b, fmt(unreal.AnimPoseExtensions.get_bone_pose(ref, b, unreal.AnimPoseSpaces.LOCAL))))
opts = unreal.AnimPoseEvaluationOptions()
for name in anims:
    anim = unreal.load_asset(C.FOLDER + "/" + name)
    pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, 0.0, opts)
    for b in ("root", "pelvis"):
        log("%s %s %s 長さ=%.2f秒" % (name, b, fmt(unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.LOCAL)), anim.get_editor_property("sequence_length")))
log("完了")
