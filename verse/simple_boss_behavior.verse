using { /Fortnite.com/AI }
using { /Fortnite.com/Animation/PlayAnimation }
using { /Fortnite.com/Characters }
using { /Fortnite.com/Game }
using { /Fortnite.com/Playspaces }
using { /Verse.org/Simulation }
using { /Verse.org/Random }
using { /Verse.org/Assets }
using { /Verse.org/SceneGraph }
using { /UnrealEngine.com/Temporary/SpatialMath }

# ボスの攻撃1種類分。アニメごとに当たる瞬間や届く距離が違うので、まとめて持つ
simple_boss_attack<public> := class<concrete>:
    @editable Anim:?animation_sequence = false
    # アニメ開始から当たるまでの秒数
    @editable HitTime:float = 1.0
    # アニメの長さ(秒)。終わるまで次の行動をしない
    @editable Length:float = 2.0
    # 当たる距離(cm)。踏み込むアニメは長めにする
    @editable Range:float = 200.0
    @editable Damage:float = 20.0

# プレイヤーを見つけたら歩いて近づき、攻撃の届く距離で Attacks からランダムに1つ選んで攻撃する。
# 待機・歩きのアニメはキャラクター定義のアニメーションプリセットが流すので、ここでは攻撃だけ流す
simple_boss_behavior<public> := class(npc_behavior):
    @editable Attacks:[]simple_boss_attack = array{}
    # この距離(cm)以内のプレイヤーを狙う
    @editable DetectRadius:float = 3000.0
    # この距離(cm)まで近づいたら攻撃を始める
    @editable AttackStartRange:float = 200.0
    # 攻撃と攻撃の間の待ち時間(秒)
    @editable AttackInterval:float = 0.8
    @editable MoveSpeedMultiplier:float = 1.0

    OnBegin<override>()<suspends>:void =
        if:
            Agent := GetAgent[]
            Me := Agent.GetFortCharacter[]
            Nav := Me.GetNavigatable[]
            Focus := Me.GetFocusInterface[]
        then:
            Nav.SetMovementSpeedMultiplier(MoveSpeedMultiplier)
            loop:
                if (not Me.IsActive[]):
                    break
                if (Target := FindTarget[Me]):
                    # 相手の方を向き続けながら追いかけて攻撃する。相手を見失ったら探し直す
                    race:
                        Focus.MaintainFocus(Target)
                        ChaseAndAttack(Me, Nav, Target)
                else:
                    Sleep(0.5)

    ChaseAndAttack(Me:fort_character, Nav:navigatable, Target:agent)<suspends>:void =
        loop:
            if (not Me.IsActive[]):
                break
            if (TargetChar := Target.GetFortCharacter[], TargetChar.IsActive[]):
                D := HorizontalDistance(Me, TargetChar)
                if (D > DetectRadius * 1.5):
                    break
                if (D <= AttackStartRange):
                    Nav.StopNavigation()
                    Attack(Me, TargetChar)
                    Sleep(AttackInterval)
                else:
                    # 相手は動くので、短い時間で区切って行き先を更新する
                    race:
                        Nav.NavigateTo(MakeNavigationTarget(Target), ?MovementType := movement_types.Walking)
                        Sleep(0.5)
            else:
                break

    Attack(Me:fort_character, TargetChar:fort_character)<suspends>:void =
        if (Picked := Attacks[GetRandomInt(0, Attacks.Length - 1)]):
            if (Anim := Picked.Anim?, Controller := Me.GetPlayAnimationController[]):
                Controller.Play(Anim, ?Layer := play_animation_layer.FullBody, ?BlendInTime := 0.2, ?BlendOutTime := 0.3)
            Sleep(Picked.HitTime)
            # 当たる瞬間に距離を見て、避けられていたら空振りにする
            if (Me.IsActive[], TargetChar.IsActive[], HorizontalDistance(Me, TargetChar) <= Picked.Range):
                TargetChar.Damage(damage_args{Instigator := option{Me}, Source := option{Me}, Amount := Picked.Damage})
            Sleep(Max(0.0, Picked.Length - Picked.HitTime))
        else:
            Sleep(1.0)

    FindTarget(Me:fort_character)<transacts><decides>:agent =
        var Best:?agent = false
        var BestDist:float = DetectRadius
        Playspace := GetEntity[].GetPlayspaceForEntity[]
        for (P : Playspace.GetPlayers(), C := P.GetFortCharacter[], C.IsActive[]):
            D := HorizontalDistance(Me, C)
            if (D < BestDist):
                set Best = option{P}
                set BestDist = D
        Best?

    HorizontalDistance(A:fort_character, B:fort_character)<transacts>:float =
        Offset := B.GetTransform().Translation - A.GetTransform().Translation
        Sqrt(Offset.X * Offset.X + Offset.Y * Offset.Y)
