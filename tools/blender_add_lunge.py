# 攻撃アニメ(大きさ焼き込み済みの FBX)に、前へ踏み込んで戻る動きを足す。手が体の近くまでしか出ない攻撃を、離れた相手に届かせるため。
# 腰を前に運び、踏み出す足は持ち上げて前へ、もう片方の足は元の位置に固定する。
# 腰を動かすと足も一緒に動いて床を滑るので、両脚は太もも・すねの2本で足首を目標に届かせる計算(2本の骨の IK)で曲げ直す。
#   blender -b -P blender_add_lunge.py -- 入力.fbx 出力.fbx 踏み出す足(l/r) 開始コマ 到達コマ 戻り始めコマ 終了コマ 踏み込み距離cm 腰の割合
import bpy, sys, json, math
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
src, dst, step_side = a[0], a[1], a[2]
f_start, f_hit, f_back, f_end = (int(x) for x in a[3:7])
dist, pelvis_ratio = float(a[7]), float(a[8])
LIFT = 12.0  # 踏み出す足を持ち上げる高さ(cm)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=src)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
act = arm.animation_data.action
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"
mw, mwi = arm.matrix_world, arm.matrix_world.inverted()

# ボスは -Y 向き
FWD = Vector((0, -1, 0))

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)

def offset(f):
    # 0 → 踏み込み → 保持 → 戻る
    if f <= f_start or f >= f_end:
        return 0.0, 0.0
    if f < f_hit:
        u = (f - f_start) / (f_hit - f_start)
        return smooth(u), math.sin(math.pi * u)
    if f <= f_back:
        return 1.0, 0.0
    u = (f - f_back) / (f_end - f_back)
    return 1.0 - smooth(u), math.sin(math.pi * u)

# 元の姿勢を全コマ記録(ワールド行列)
names = [b.name for b in arm.data.bones]
orig = {}
for f in range(f0, f1 + 1):
    scn.frame_set(f)
    orig[f] = {n: (mw @ arm.pose.bones[n].matrix).copy() for n in names}

new_act = bpy.data.actions.new("Lunge")
arm.animation_data.action = new_act
if hasattr(arm.animation_data, "action_slot") and new_act.slots:
    arm.animation_data.action_slot = new_act.slots[0]

def set_world(name, m):
    arm.pose.bones[name].matrix = mwi @ m
    bpy.context.view_layer.update()

def solve_leg(side, o, foot_target):
    thigh, calf, foot = "thigh_" + side, "calf_" + side, "foot_" + side
    H = (mw @ arm.pose.bones[thigh].matrix).to_translation()  # 腰が動いた後の股関節
    oH, oK, oF = o[thigh].to_translation(), o[calf].to_translation(), o[foot].to_translation()
    la, lb = (oK - oH).length, (oF - oK).length
    to_t = foot_target - H
    d = min(to_t.length, la + lb - 0.01)
    dirt = to_t.normalized()
    # 膝の曲がる向きは元の姿勢の膝の向きを使う
    bend = (oK - oH) - (oK - oH).project(oF - oH)
    if bend.length < 1e-4:
        bend = FWD.copy()
    bend = (bend - bend.project(dirt)).normalized()
    x = (la * la - lb * lb + d * d) / (2 * d)
    h = math.sqrt(max(0.0, la * la - x * x))
    K = H + dirt * x + bend * h
    T = H + dirt * d
    for name, p0, p1, q0, q1 in ((thigh, H, K, oH, oK), (calf, K, T, oK, oF)):
        r = (q1 - q0).normalized().rotation_difference((p1 - p0).normalized())
        m = o[name]
        rot = r.to_matrix().to_4x4() @ m.to_3x3().normalized().to_4x4()
        rot.translation = p0
        set_world(name, rot)
    # 足首から先は元の向きのまま
    fm = o[foot].copy()
    fm.translation = T
    set_world(foot, fm)

back = "r" if step_side == "l" else "l"
for i, f in enumerate(range(f0, f1 + 1)):
    o = orig[f]
    k, lift = offset(f)
    # 親の姿勢が更新されてからでないと子の行列が正しく入らないので、1本ずつ更新する
    for n in names:
        arm.pose.bones[n].matrix = mwi @ o[n]
        bpy.context.view_layer.update()
    pm = o["pelvis"].copy()
    pm.translation = pm.translation + FWD * dist * pelvis_ratio * k
    set_world("pelvis", pm)
    # 腰を動かすと上半身・脚は付いてくる。脚は足首の目標へ曲げ直す
    solve_leg(step_side, o, o["foot_" + step_side].to_translation() + FWD * dist * k + Vector((0, 0, LIFT * lift)))
    solve_leg(back, o, o["foot_" + back].to_translation())
    for pb in arm.pose.bones:
        for p in ("location", "rotation_quaternion", "scale"):
            pb.keyframe_insert(p, frame=1 + i)
bpy.data.actions.remove(act)
n = f1 - f0 + 1
scn.frame_start, scn.frame_end = 1, n

# 確認: 固定した足の動き(元との差)と、手の最大到達
err = 0.0
reach = 0.0
for f in range(1, n + 1):
    scn.frame_set(f)
    err = max(err, ((mw @ arm.pose.bones["foot_" + back].head) - orig[f0 + f - 1]["foot_" + back].to_translation()).length)
    for hnd in ("hand_l", "hand_r"):
        reach = max(reach, -(mw @ arm.pose.bones[hnd].head).y)
bpy.ops.export_scene.fbx(filepath=dst, use_selection=False, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL', object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
    bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0, path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE')
print("RESULT " + json.dumps({"frames": n, "planted_foot_err_cm": round(err, 2), "max_hand_reach_cm": round(reach)}))
