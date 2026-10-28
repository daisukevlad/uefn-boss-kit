# 他のキャラ用のアニメを、ボス(大きさ焼き込み済みの anims_ue の FBX)の骨に移し替えて書き出す。
# 対応: Mixamo の FBX / UE5 Manny の FBX(市販・無料のモーションキャプチャ)/ Kimodo の BVH(SOMA の骨)
# 休みの姿勢が違う(元は T ポーズ等、ボスは腕を前に下ろした姿勢)ので、骨の向きを休みの姿勢どうしでそろえてから、
# 元の動いた分(ワールドでの回転差)をボスの骨に足す。指は移さない(ボスの休みの形のまま)。
#   blender -b -P blender_retarget_motion.py -- 元.fbx|元.bvh ボス.fbx 出力.fbx [確認用.blend]
import bpy, sys, json
from mathutils import Matrix

a = sys.argv[sys.argv.index("--") + 1:]
src_path, tgt_path, dst = a[0], a[1], a[2]
blend_out = a[3] if len(a) > 3 else None

LIMBS = {
    "clavicle_l": "clavicle_l", "upperarm_l": "upperarm_l", "lowerarm_l": "lowerarm_l", "hand_l": "hand_l",
    "clavicle_r": "clavicle_r", "upperarm_r": "upperarm_r", "lowerarm_r": "lowerarm_r", "hand_r": "hand_r",
    "thigh_l": "thigh_l", "calf_l": "calf_l", "foot_l": "foot_l", "ball_l": "ball_l",
    "thigh_r": "thigh_r", "calf_r": "calf_r", "foot_r": "foot_r", "ball_r": "ball_r",
}
# Manny は背骨が5本・首が2本あり、ボスは背骨3本・首1本なので、間の骨は移さない(親子の回転で形は付いてくる)
MANNY = dict(LIMBS, pelvis="pelvis", spine_01="spine_01", spine_03="spine_02", spine_05="spine_03",
             neck_01="neck_01", head="head")
MIXAMO = {
    "Hips": "pelvis", "Spine": "spine_01", "Spine1": "spine_02", "Spine2": "spine_03",
    "Neck": "neck_01", "Head": "head",
    "LeftShoulder": "clavicle_l", "LeftArm": "upperarm_l", "LeftForeArm": "lowerarm_l", "LeftHand": "hand_l",
    "RightShoulder": "clavicle_r", "RightArm": "upperarm_r", "RightForeArm": "lowerarm_r", "RightHand": "hand_r",
    "LeftUpLeg": "thigh_l", "LeftLeg": "calf_l", "LeftFoot": "foot_l", "LeftToeBase": "ball_l",
    "RightUpLeg": "thigh_r", "RightLeg": "calf_r", "RightFoot": "foot_r", "RightToeBase": "ball_r",
}
MIXAMO = {"mixamorig:" + k: v for k, v in MIXAMO.items()}
SOMA = {
    "Hips": "pelvis", "Spine1": "spine_01", "Chest": "spine_03",
    "Neck1": "neck_01", "Head": "head",
    "LeftShoulder": "clavicle_l", "LeftArm": "upperarm_l", "LeftForeArm": "lowerarm_l", "LeftHand": "hand_l",
    "RightShoulder": "clavicle_r", "RightArm": "upperarm_r", "RightForeArm": "lowerarm_r", "RightHand": "hand_r",
    "LeftLeg": "thigh_l", "LeftShin": "calf_l", "LeftFoot": "foot_l", "LeftToeBase": "ball_l",
    "RightLeg": "thigh_r", "RightShin": "calf_r", "RightFoot": "foot_r", "RightToeBase": "ball_r",
}
# Mesh2Motion(GLB)は1ファイルに複数のアニメが入っているので「ファイル.glb#アニメ名」で選ぶ。骨はボスと同じ名前
SAME = {k: k for k in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head")}
SAME.update(LIMBS)
src_action = None
if "#" in src_path:
    src_path, src_action = src_path.split("#", 1)
IS_BVH = src_path.lower().endswith(".bvh")
IS_GLB = src_path.lower().endswith((".glb", ".gltf"))

def import_src():
    if IS_BVH:
        bpy.ops.import_anim.bvh(filepath=src_path, update_scene_fps=True, update_scene_duration=False)
    elif IS_GLB:
        bpy.ops.import_scene.gltf(filepath=src_path)
        arm = [o for o in bpy.context.selected_objects if o.type == "ARMATURE"][0]
        arm.animation_data_create()
        # 読み込んだ全アニメが NLA に積まれて混ざるので外す
        for tr in list(arm.animation_data.nla_tracks):
            arm.animation_data.nla_tracks.remove(tr)
        arm.animation_data.action = bpy.data.actions[src_action]
        if bpy.app.version >= (4, 4, 0) and arm.animation_data.action.slots:
            arm.animation_data.action_slot = arm.animation_data.action.slots[0]
    else:
        bpy.ops.import_scene.fbx(filepath=src_path)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
scn.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=tgt_path)
tgt = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
before = set(bpy.data.objects)
import_src()
src_objs = [o for o in bpy.data.objects if o not in before]
src = [o for o in src_objs if o.type == "ARMATURE" and o.animation_data and o.animation_data.action][0]
names = set(src.data.bones.keys())
MAP = SOMA if IS_BVH else MIXAMO if "mixamorig:Hips" in names else MANNY if "spine_05" in names else SAME
missing = [s for s in MAP if s not in names]
if missing:
    raise RuntimeError("元の骨にない: " + ", ".join(missing))
HIPS = next(k for k, v in MAP.items() if v == "pelvis")
s_act = src.animation_data.action
f0, f1 = int(s_act.frame_range[0]), int(s_act.frame_range[1])
fps = scn.render.fps  # 元のアニメの fps(読み込みで設定される)

if tgt.animation_data and tgt.animation_data.action:
    bpy.data.actions.remove(tgt.animation_data.action)
tgt.animation_data_create()
for pb in tgt.pose.bones:
    pb.rotation_mode = "QUATERNION"
    pb.location, pb.rotation_quaternion, pb.scale = (0, 0, 0), (1, 0, 0, 0), (1, 1, 1)

def rot(m):
    return m.to_3x3().normalized().to_quaternion()

def world_dir(obj, bone):
    return ((obj.matrix_world @ bone.tail_local) - (obj.matrix_world @ bone.head_local)).normalized()

# 休みの姿勢での骨の向きをそろえる回転(元の骨の向き → ボスの骨の向き)と、休みの姿勢のワールド回転
pre = {}
for s, t in MAP.items():
    sb, tb = src.data.bones[s], tgt.data.bones[t]
    d = world_dir(src, sb).rotation_difference(world_dir(tgt, tb))
    pre[s] = (d, rot(src.matrix_world @ sb.matrix_local), rot(tgt.matrix_world @ tb.matrix_local))

hips_rest = src.matrix_world @ src.data.bones[HIPS].head_local
pelvis_rest = tgt.matrix_world @ tgt.data.bones["pelvis"].head_local
ratio = (pelvis_rest.z - (tgt.matrix_world @ tgt.data.bones["root"].head_local).z) / hips_rest.z

order = [b.name for b in tgt.data.bones]  # 親から順に並んでいる
inv_t = tgt.matrix_world.inverted()
for i, f in enumerate(range(f0, f1 + 1)):
    scn.frame_set(f)
    want = {}
    for s, t in MAP.items():
        d, s_rest, t_rest = pre[s]
        s_now = rot(src.matrix_world @ src.pose.bones[s].matrix)
        want[t] = s_now @ s_rest.inverted() @ d.inverted() @ t_rest
    hips_now = src.matrix_world @ src.pose.bones[HIPS].head
    pelvis_pos = pelvis_rest + (hips_now - hips_rest) * ratio
    for name in order:
        if name not in want:
            continue
        pb = tgt.pose.bones[name]
        bpy.context.view_layer.update()
        cur = tgt.matrix_world @ pb.matrix
        pos = pelvis_pos if name == "pelvis" else cur.to_translation()
        m = Matrix.LocRotScale(pos, want[name], cur.to_scale())
        pb.matrix = inv_t @ m
    bpy.context.view_layer.update()
    for pb in tgt.pose.bones:
        pb.keyframe_insert("location", frame=1 + i)
        pb.keyframe_insert("rotation_quaternion", frame=1 + i)
        pb.keyframe_insert("scale", frame=1 + i)
tgt.animation_data.action.name = "Retarget"
n = f1 - f0 + 1

for o in src_objs:
    bpy.data.objects.remove(o, do_unlink=True)
scn.render.fps = fps
scn.frame_start, scn.frame_end = 1, n
bpy.ops.export_scene.fbx(filepath=dst, use_selection=False, global_scale=1.0, apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL', object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
    bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0, path_mode='COPY', embed_textures=True, mesh_smooth_type='FACE')
if blend_out:
    # 見比べ用に元のアニメを横に置く
    import_src()
    for o in bpy.context.selected_objects:
        if o.parent is None:
            o.location.x += 300
    scn.render.fps = fps
    scn.frame_start, scn.frame_end = 1, n
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
print("RESULT " + json.dumps({"frames": n, "fps": fps, "sec": round(n / fps, 2), "ratio": round(ratio, 3), "map": "SOMA" if MAP is SOMA else "MIXAMO" if MAP is MIXAMO else "MANNY" if MAP is MANNY else "SAME"}))
