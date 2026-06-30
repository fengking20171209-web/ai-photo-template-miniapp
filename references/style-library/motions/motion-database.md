# MotionDNA — 结构化动作语义系统 v2.0

> 版本：v2.0 | 创建：2026-05-28 | 五段式动作拆解

---

## 动作拆解体系说明

每个动作按 **HEAD / TORSO / HIP / LEGS / HANDS** 五段式拆解，
配合动态修饰词和适配标签，确保动作描述精确可复用。

---

## 01. STANDING_NEUTRAL — 自然站立

### HEAD
head_neutral, gaze_camera, chin_level

### TORSO
torso_upright, shoulders_relaxed, chest_open

### HIP
pelvis_neutral, weight_even

### LEGS
feet_shoulder_width, weight_even, knees_relaxed

### HANDS
arms_relaxed_sides, fingers_natural

### 动态修饰
still, relaxed, natural

### 适配
情绪：confident + editorial
服装：全品类通用
镜头：全身 + 半身

---

## 02. LOOKBACK_BEND — 回头弯腰

### HEAD
head_turn_right_30deg, gaze_camera, chin_tilt_down

### TORSO
torso_twist_45deg, torso_bend_forward_20deg, lumbar_curve_exaggerated

### HIP
pelvis_tilt_back, hip_push_back, weight_shift_right

### LEGS
one_leg_forward, weight_on_back_leg, knee_slight_bend

### HANDS
hand_on_hip, brush_hair_back

### 动态修饰
dynamic, mid-motion, captured

### 适配
情绪：confident + mysterious
服装：lace + silk
镜头：low_angle + 85mm

---

## 03. POOLSIDE_RECLINE — 泳池边侧卧

### HEAD
head_resting_hand, gaze_soft, chin_tilt_up_10deg

### TORSO
torso_lateral_bend, torso_reclined_60deg, ribcage_open

### HIP
pelvis_shifted_left, hip_pushed_out, weight_on_left_hip

### LEGS
legs_extended_right, one_leg_crossed, ankle_relaxed

### HANDS
left_arm_supporting_upper, right_hand_on_thigh

### 动态修饰
relaxed, languid, poolside

### 适配
情绪：playful + confident
服装：swimwear
镜头：low_angle + 35mm全身

---

## 04. EDITORIAL_STAND — 杂志定点

### HEAD
head_tilt_back_10deg, gaze_camera_intense, jaw_defined

### TORSO
torso_upright_proud, shoulders_back, chest_expanded

### HIP
pelvis_anterior_tilt, hip_shift_one_side, weight_on_one_leg

### LEGS
contrapposto_stance, one_leg_straight, one_leg_bent

### HANDS
one_arm_on_hip, other_arm_relaxed, or_crossed_arms

### 动态修饰
powerful, editorial, commanding

### 适配
情绪：dominant + editorial
服装：全品类
镜头：50mm半身 + 35mm全身

---

## 05. RUNWAY_WALK — T台步态

### HEAD
head_high, gaze_forward, chin_level, expression_fierce

### TORSO
torso_upright_dynamic, shoulders_back, core_engaged

### HIP
hip_sway_dynamic, weight_shifting, pelvis_forward

### LEGS
stride_forward, one_leg_ahead, toes_pointed, heels_high

### HANDS
arms_swinging_naturally, or_hand_on_hip, or_touching_hair

### 动态修饰
walking, mid-stride, dynamic, fashion

### 适配
情绪：confident + dominant
服装：全品类，尤其lace + sportswear
镜头：35mm全身 + low_angle

---

## 06. CANDID_MOTION — 抓拍动态

### HEAD
head_turned_away_20deg, gaze_averted, expression_natural

### TORSO
torso_slight_twist, natural_gesture, unposed

### HIP
hip_shift_natural, weight_in_transition

### LEGS
mid_step, one_foot_ahead, natural_gait

### HANDS
adjusting_hair, touching_face, holding_object, gesturing

### 动态修饰
candid, unposed, natural, spontaneous

### 适配
情绪：candid + playful
服装：全品类
镜头：50mm + 85mm

---

## 07. SEATED_CROSS — 盘腿坐

### HEAD
head_neutral, gaze_soft, expression_relaxed

### TORSO
torso_upright, slight_forward_lean, shoulders_relaxed

### HIP
pelvis_ground, sitting_flat, legs_crossed

### LEGS
crossed_on_ground, or_on_chair, feet_relaxed

### HANDS
resting_on_knees, or_holding_chin, or_playing_with_hair

### 动态修饰
seated, relaxed, intimate

### 适配
情绪：candid + mysterious
服装：lace + nude
镜头：50mm半身 + 微距

---

## 08. LEANING_WALL — 靠墙站立

### HEAD
head_against_wall, gaze_camera, chin_slight_tilt

### TORSO
torso_against_surface, shoulders_back, relaxed

### HIP
hip_shifted, one_hip_forward, weight_on_one_leg

### LEGS
one_leg_bent_foot_on_wall, other_leg_straight

### HANDS
hand_on_wall, or_in_pocket, or_touching_hair

### 动态修饰
casual, leaning, urban

### 适配
情绪：confident + candid
服装：sportswear + cyberwear
镜头：35mm全身 + 50mm半身

---

## 09. TWIST_TURN — 转身回眸

### HEAD
head_turned_180deg, gaze_over_shoulder, chin_tilt_down

### TORSO
torso_twisted_90deg, back_arched_slight, shoulder_line_visible

### HIP
pelvis_facing_forward, hip_twisted, S_curve

### LEGS
weight_on_one_leg, other_leg_relaxed, hip_jutted

### HANDS
one_hand_on_hip, other_hand_extended, or_touching_hair

### 动态修饰
turning, dynamic, caught_in_motion

### 适配
情绪：mysterious + confident
服装：lace + silk
镜头：85mm + 50mm

---

## 10. WALKING_BACK — 背影行走

### HEAD
head_forward, gaze_ahead, back_of_head_visible

### TORSO
torso_upright_walking, back_visible, shoulders_defined

### HIP
hip_sway_walking, weight_shifting

### LEGS
stride_forward, back_of_legs_visible, calves_defined

### HANDS
arms_swinging, or_hair_being_caught_by_wind

### 动态修饰
walking_away, mysterious, departing

### 适配
情绪：mysterious + editorial
服装：全品类
镜头：35mm全身 + 135mm长焦

---

## 11. DEEP_SQUAT — 深蹲低机位

### HEAD
head_neutral, gaze_camera, chin_level_or_up

### TORSO
torso_upright, chest_open, core_engaged

### HIP
pelvis_low, hip_flexed, weight_centered

### LEGS
deep_squat, thighs_parallel, knees_over_toes

### HANDS
hands_on_knees, or_between_legs, or_touching_ground

### 动态修饰
power, grounded, athletic

### 适配
情绪：energetic + dominant
服装：sportswear + swimwear
镜头：low_angle + 35mm

---

## 12. OVERHEAD_REACH — 举手伸展

### HEAD
head_back, gaze_up, arms_extended

### TORSO
torso_extended, back_arched_slight, ribcage_expanded

### HIP
pelvis_forward, hip_thrust_slight

### LEGS
feet_together, or_one_ahead, weight_on_toes

### HANDS
both_arms_overhead, stretching, or_holding_hair

### 动态修饰
stretching, elongated, editorial

### 适配
情绪：confident + energetic
服装：sportswear + swimwear
镜头：35mm全身 + 24mm广角

---

## 13. FLOOR_POSE — 地面姿态

### HEAD
head_resting_arm, gaze_camera, expression_soft

### TORSO
torso_lateral, lying_on_side, or_on_stomach

### HIP
hip_on_ground, weight_on_side

### LEGS
legs_extended, or_bent_knee, elegant_stacking

### HANDS
supporting_head, or_stretched_out, or_near_face

### 动态修饰
lying, relaxed, intimate, editorial

### 适配
情绪：candid + mysterious
服装：lace + nude + silk
镜头：50mm + 微距

---

## 14. HAIR_FLIP — 甩发动态

### HEAD
head_turning, hair_in_motion, chin_up

### TORSO
torso_slight_twist, dynamic, momentum_visible

### HIP
hip_shifted, weight_in_transition

### LEGS
mid_stride, or_standing_dynamic

### HANDS
hand_in_hair, or_just_released_hair

### 动态修饰
hair_movement, dynamic, dramatic, caught_in_air

### 适配
情绪：confident + energetic
服装：全品类
镜头：85mm + 135mm

---

## 15. SIDE_POSE — 侧身展示

### HEAD
head_profile_or_three_quarter, gaze_ahead_or_camera

### TORSO
torso_profile, one_shoulder_forward, S_line

### HIP
hip_pushed_out, accentuating_curve

### LEGS
one_leg_ahead, weight_on_back_leg

### HANDS
one_hand_on_hip, other_relaxed

### 动态修饰
side_view, profile, curvaceous

### 适配
情绪：confident + editorial
服装：全品类
镜头：50mm + 85mm

---

## 16. HANDS_BEHIND_HEAD — 双手抱头

### HEAD
head_neutral_or_back, gaze_camera, chin_up

### TORSO
torso_expanded, chest_open, elbows_out

### HIP
hip_shifted, one_hip_forward

### LEGS
contrapposto, weight_one_leg

### HANDS
both_hands_behind_head, elbows_wide

### 动态修饰
confident, posed, fashion

### 适配
情绪：confident + dominant
服装：swimwear + sportswear
镜头：50mm + 35mm

---

## 17. KNEELING — 跪姿

### HEAD
head_neutral, gaze_camera_or_down, expression_soft

### TORSO
torso_upright, or_slight_lean, shoulders_relaxed

### HIP
pelvis_on_heels, or_one_knee_up

### LEGS
both_knees_down, or_one_knee_up_one_down

### HANDS
on_thighs, or_between_legs, or_touching_ground

### 动态修饰
kneeling, soft, submissive_or_powerful

### 适配
情绪：mysterious + playful
服装：lace + sportswear
镜头：50mm + low_angle

---

## 18. ARCHA_BACK — 后仰弓身

### HEAD
head_back, hair_falling_back, gaze_up_or_closed

### TORSO
torso_arched, back_bent, chest_expanded

### HIP
hip_forward, pelvis_pushed

### LEGS
standing_or_kneeling, weight_centered

### HANDS
on_hips, or_on_ground_supporting, or_overhead

### 动态修饰
dramatic, arched, expressive

### 适配
情绪：confident + luxurious
服装：lace + silk
镜头：85mm + 50mm

---

## 19. DANCE_SPIN — 旋转舞蹈

### HEAD
head_turning, hair_flying, expression_joyful

### TORSO
torso_rotating, dynamic_blur_slight

### HIP
hip_rotating, momentum_visible

### LEGS
spinning, one_leg_pivot, dress_flying

### HANDS
arms_extended, or_holding_skirt, or_fluid

### 动态修饰
spinning, joyful, flowing, dynamic

### 适配
情绪：playful + energetic
服装：silk + lace
镜头：35mm全身 + 50mm

---

## 20. INTIMATE_GAZE — 近距离凝视

### HEAD
head_close_to_camera, gaze_intense, eyes_near

### TORSO
torso_close, face_filling_frame, intimate

### HIP
N/A (面部特写为主)

### LEGS
N/A

### HANDS
near_face, touching_lips, framing_face

### 动态修饰
intimate, close, intense, emotional

### 适配
情绪：mysterious + confident
服装：不重要（面部为主）
镜头：85mm贴脸 + 微距

---

## 21. BACK_ARCH_STANDING — 站立后弓

### HEAD
head_back, hair_falling, gaze_up

### TORSO
torso_arched_back_30deg, chest_expanded, spine_curve

### HIP
pelvis_forward, hip_pushed_ahead

### LEGS
standing_straight, weight_centered

### HANDS
on_hips, or_behind_back, or_overhead

### 动态修饰
dramatic, powerful, editorial

### 适配
情绪：confident + dominant
服装：lace + cyberwear
镜头：35mm全身 + low_angle

---

## 22. OVER_SHOULDER — 回眸侧身

### HEAD
head_turned_120deg, gaze_over_shoulder, expression_knowing

### TORSO
torso_3_quarter_view, back_partially_visible

### HIP
hip_visible_from_behind, curve_accentuated

### LEGS
weight_on_one_leg, other_relaxed

### HANDS
one_hand_on_hip, or_touching_hair

### 动态修饰
looking_back, mysterious, inviting

### 适配
情绪：mysterious + confident
服装：lace + silk
镜头：85mm + 50mm
