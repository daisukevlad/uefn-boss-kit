# 攻撃アニメ(大きさ焼き込み済みの FBX)から、ボスの Verse(simple_boss_attack)に入れる値を測る。
#   HitTime: 手の速さが一番大きいコマ(振り抜く瞬間)の秒数
#   Length : アニメの長さ(秒)。UEFN では1コマ短く数えられるので、その値も出す
#   Range  : 当たる瞬間の手の前方距離 + 余裕(体の太さの分)
#   blender -b -P blender_measure_attack.py -- 攻撃.fbx [余裕cm(既定 50)]
import bpy, sys, json

a = sys.argv[sys.argv.index("--") + 1:]
src = a[0]
margin = float(a[1]) if len(a) > 1 else 50.0

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=src)
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
act = arm.animation_data.action
f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
fps = scn.render.fps / scn.render.fps_base

prev = {}
best_speed, best_frame, best_hand = 0.0, f0, ""
reach_at = {}
for f in range(f0, f1 + 1):
    scn.frame_set(f)
    pelvis = arm.matrix_world @ arm.pose.bones["pelvis"].head
    for hand in ("hand_l", "hand_r"):
        p = arm.matrix_world @ arm.pose.bones[hand].head
        if hand in prev:
            speed = (p - prev[hand]).length * fps / 100.0  # m/秒
            if speed > best_speed:
                best_speed, best_frame, best_hand = speed, f, hand
        prev[hand] = p
        # ボスの前は -Y。体の中心(原点)から前にどれだけ出ているか
        reach_at[(f, hand)] = -p.y

frames = f1 - f0 + 1
hit_reach = reach_at[(best_frame, best_hand)]
max_reach = max(v for (f, h), v in reach_at.items())
print("RESULT " + json.dumps({
    "HitTime": round((best_frame - f0) / fps, 2),
    "Length": round(frames / fps, 2),
    "Length_in_UEFN": round((frames - 1) / fps, 2),
    "Range": round(max(hit_reach, 0) + margin),
    "hand": best_hand,
    "hand_speed_m_s": round(best_speed, 1),
    "reach_at_hit_cm": round(hit_reach),
    "max_reach_cm": round(max_reach),
}))
