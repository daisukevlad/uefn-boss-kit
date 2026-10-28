# ループ再生するアニメ(大きさ焼き込み済みの FBX)を、指定コマで切り、最後の数コマを最初の姿勢へなめらかに寄せて、つなぎ目で途切れないようにする。
# 切るコマは loop_measure で「最初の姿勢に一番近いコマ」を探して決める。元ファイルは変更しない。
#   blender -b -P blender_make_loop.py -- 入力.fbx 出力.fbx 切るコマ 寄せるコマ数
import bpy, sys, json
a = sys.argv[sys.argv.index("--") + 1:]
src, dst, cut, blend = a[0], a[1], int(a[2]), int(a[3])
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=src)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
old = arm.animation_data.action
first = int(old.frame_range[0])
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"

def sample(f):
    scn.frame_set(f)
    return {pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in arm.pose.bones}

# 最後のコマ(cut)は最初のコマと同じ姿勢になる前提で捨てる(ループで最初のコマに戻るため)
poses = [sample(f) for f in range(first, cut)]
start = poses[0]
n = len(poses)
for i in range(blend):
    idx = n - blend + i
    w = (i + 1) / (blend + 1)
    p = poses[idx]
    for name, (loc, rot, sca) in p.items():
        sl, sr, ss = start[name]
        r = rot.slerp(sr if rot.dot(sr) >= 0 else -sr, w)
        p[name] = (loc.lerp(sl, w), r, sca.lerp(ss, w))

new = bpy.data.actions.new(old.name.split("|")[-1] + "_loop")
arm.animation_data.action = new
for i, pose in enumerate(poses):
    for pb in arm.pose.bones:
        loc, rot, sca = pose[pb.name]
        pb.location, pb.rotation_quaternion, pb.scale = loc, rot, sca
        pb.keyframe_insert("location", frame=1 + i); pb.keyframe_insert("rotation_quaternion", frame=1 + i); pb.keyframe_insert("scale", frame=1 + i)
bpy.data.actions.remove(old)
scn.frame_start, scn.frame_end = 1, n
bpy.ops.export_scene.fbx(filepath=dst, use_selection=False, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL', object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
    bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0, path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE')
print("RESULT " + json.dumps({"frames": n, "sec": round(n / scn.render.fps, 2)}))
