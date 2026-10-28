# 攻撃アニメ(大きさ焼き込み済みの FBX)を切り出し、振りかぶりの頂点で溜め、振り下ろしを速め、当たった瞬間に止めて迫力を出す。
# 頂点 = 区間内で手が一番高いコマ、当たり = 頂点より後で手が一番低いコマ。元ファイルは変更しない。
#   blender -b -P blender_retime_attack.py -- 入力.fbx 出力.fbx 開始秒 終了秒 振り下ろし倍速 溜めコマ 止めコマ
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]
src, dst = a[0], a[1]
t0, t1, speed, hold_top, hold_hit = float(a[2]), float(a[3]), float(a[4]), int(a[5]), int(a[6])
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=src)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
old = arm.animation_data.action
fps = scn.render.fps
first = int(old.frame_range[0])
f0, f1 = first + round(t0 * fps), first + round(t1 * fps)

def hand_z(f):
    scn.frame_set(f)
    return min((arm.matrix_world @ arm.pose.bones[b].head).z for b in ("hand_l", "hand_r")), max((arm.matrix_world @ arm.pose.bones[b].head).z for b in ("hand_l", "hand_r"))
zs = {f: hand_z(f) for f in range(f0, f1 + 1)}
top = max(zs, key=lambda f: zs[f][1])
hit = min((f for f in zs if f > top), key=lambda f: zs[f][0])

# 新しいコマ → 元の時刻(小数コマ)の対応表
times = [float(f) for f in range(f0, top)]
times += [float(top)] * (hold_top + 1)
n = max(1, round((hit - top) / speed))
times += [top + (hit - top) * i / n for i in range(1, n + 1)]
times += [float(hit)] * hold_hit
times += [float(f) for f in range(hit + 1, f1 + 1)]

# 元の時刻で姿勢を評価して、新しいアクションに焼き直す
poses = []
for t in times:
    scn.frame_set(int(t), subframe=t - int(t))
    poses.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in arm.pose.bones})
new = bpy.data.actions.new(old.name.split("|")[-1] + "_retimed")
arm.animation_data.action = new
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"
for i, pose in enumerate(poses):
    for pb in arm.pose.bones:
        loc, rot, sca = pose[pb.name]
        pb.location, pb.rotation_quaternion, pb.scale = loc, rot, sca
        pb.keyframe_insert("location", frame=1 + i); pb.keyframe_insert("rotation_quaternion", frame=1 + i); pb.keyframe_insert("scale", frame=1 + i)
bpy.data.actions.remove(old)
scn.frame_start, scn.frame_end = 1, len(poses)
bpy.ops.export_scene.fbx(filepath=dst, use_selection=False, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL', object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
    bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0, path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE')
print("RESULT " + json.dumps({"src_top": top - f0, "src_hit": hit - f0, "new_frames": len(poses), "new_sec": round(len(poses) / fps, 2),
    "new_hit_sec": round((times.index(float(hit)) ) / fps, 2), "hit_hand_z": round(zs[hit][0], 1)}))
