# boss_config.py のボス用に、アニメーションプリセット(AP_<ボス名>)と見た目の Blueprint(BP_<ボス名>)を作る。
# 公式手順では、カスタムキャラクターは AnimPreset の子を作って自分のアニメを入れる。元の AnimPreset_BipedLocomotion は中身が空。
# アニメの割り当てとメッシュの向きはこの後 MCP から設定する。同じ名前のものが既にあれば止める。
import os
import sys
import importlib
import unreal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import boss_config as C
importlib.reload(C)

def log(msg):
    unreal.log_warning("BOSS_ASSETS " + msg)

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mesh_path = C.FOLDER + "/" + C.MESH_NAME
if not lib.does_asset_exist(mesh_path):
    raise RuntimeError("メッシュがない: " + mesh_path + "(先に boss_import.py)")

def create_bp(name, parent):
    path = C.FOLDER + "/" + name
    if lib.does_asset_exist(path):
        raise RuntimeError("既にある: " + path)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    bp = tools.create_asset(name, C.FOLDER, unreal.Blueprint, factory)
    if not bp:
        raise RuntimeError("作れなかった: " + path)
    return bp

preset_parent = unreal.load_object(None, "/AnimPresets/AnimPreset_BipedLocomotion.AnimPreset_BipedLocomotion_C")
if not preset_parent:
    raise RuntimeError("AnimPreset_BipedLocomotion が読めない")
ap = create_bp(C.AP_NAME, preset_parent)
unreal.BlueprintEditorLibrary.compile_blueprint(ap)
lib.save_asset(C.FOLDER + "/" + C.AP_NAME)
log("作成: " + C.FOLDER + "/" + C.AP_NAME)

bp = create_bp(C.BP_NAME, unreal.Actor)
subsys = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
root = subsys.k2_gather_subobject_data_for_blueprint(bp)[0]
handle, fail = subsys.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.SkeletalMeshComponent, blueprint_context=bp))
if not fail.is_empty():
    raise RuntimeError("コンポーネントを追加できなかった: " + str(fail))
subsys.rename_subobject(handle, unreal.Text("BossMesh"))
comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle))
comp.set_editor_property("skeletal_mesh_asset", unreal.load_asset(mesh_path))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
lib.save_asset(C.FOLDER + "/" + C.BP_NAME)
log("作成: " + C.FOLDER + "/" + C.BP_NAME)
