# Tripo の FBX を UE 向けに直す。シーン単位を cm にして、大きさをメッシュ・骨の長さ・骨の移動キーに焼き込み、
# どのノードにも倍率が残らない FBX を書き出す。元ファイルは変更しない。
import bpy, sys, json
args = sys.argv[sys.argv.index("--") + 1:]
src, dst, size = args[0], args[1], float(args[2])

def fcurves(action):
    # Blender 5.0 で Action.fcurves がなくなり、キーはレイヤー → ストリップ → チャンネルバッグの中に入った
    if hasattr(action, "fcurves"):
        return list(action.fcurves)
    return [fc for layer in action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=src)
scn = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
mesh = [o for o in bpy.data.objects if o.type == "MESH"][0]
act = arm.animation_data.action
info = {"src_fps": scn.render.fps, "src_fps_base": scn.render.fps_base, "src_frames": list(act.frame_range)}
# メートル → cm(100 倍)と、ボスの大きさ(size 倍)
k = 100.0 * size
scn.unit_settings.system = 'METRIC'
scn.unit_settings.scale_length = 0.01
arm.scale = (arm.scale[0] * k, arm.scale[1] * k, arm.scale[2] * k)
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True); mesh.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
# 倍率の確定はアクションの移動キーには反映されないため、同じ倍率を掛ける
for fc in fcurves(act):
    if fc.data_path.endswith(".location"):
        for kp in fc.keyframe_points:
            kp.co[1] *= k; kp.handle_left[1] *= k; kp.handle_right[1] *= k
scn.frame_start, scn.frame_end = int(act.frame_range[0]), int(act.frame_range[1])
bpy.ops.export_scene.fbx(filepath=dst, use_selection=False, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL', object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
    bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0, path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE')
# 読み直して確かめる(同じく cm 単位のシーンで読む)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=dst)
arm2 = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
mesh2 = [o for o in bpy.data.objects if o.type == "MESH"][0]
act2 = arm2.animation_data.action
rs = sorted({round(p.co[1], 4) for fc in fcurves(act2) if fc.data_path == 'pose.bones["root"].scale' for p in fc.keyframe_points})
info.update({"out_arm_scale": [round(v, 4) for v in arm2.scale], "out_mesh_scale": [round(v, 4) for v in mesh2.scale],
    "out_mesh_dims": [round(v, 2) for v in mesh2.dimensions], "out_pelvis_head": [round(v, 2) for v in arm2.data.bones["pelvis"].head_local],
    "out_root_scale_keys": rs, "out_frames": list(act2.frame_range), "out_fps": bpy.context.scene.render.fps})
print("RESULT " + json.dumps(info))
