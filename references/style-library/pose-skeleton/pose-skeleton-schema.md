# PoseSkeleton — OpenPose 兼容骨架系统 v2.0

> 版本：v2.0 | 创建：2026-05-28 | OpenPose-compatible JSON Schema

---

## 概述

PoseSkeleton 提供标准化的骨架描述格式，
可与 ControlNet OpenPose 模型配合使用，
也可作为 Prompt 中动作描述的精确参考。

---

## JSON Schema 定义

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PoseSkeleton",
  "description": "OpenPose-compatible pose skeleton for fashion photography",
  "type": "object",
  "required": ["pose_id", "name_cn", "name_en", "keypoints", "body_segments"],
  "properties": {
    "pose_id": {
      "type": "string",
      "description": "Unique pose identifier"
    },
    "name_cn": {
      "type": "string",
      "description": "Chinese name"
    },
    "name_en": {
      "type": "string",
      "description": "English name"
    },
    "keypoints": {
      "type": "object",
      "description": "OpenPose keypoint positions",
      "properties": {
        "nose": { "$ref": "#/definitions/point2d" },
        "neck": { "$ref": "#/definitions/point2d" },
        "r_shoulder": { "$ref": "#/definitions/point2d" },
        "r_elbow": { "$ref": "#/definitions/point2d" },
        "r_wrist": { "$ref": "#/definitions/point2d" },
        "l_shoulder": { "$ref": "#/definitions/point2d" },
        "l_elbow": { "$ref": "#/definitions/point2d" },
        "l_wrist": { "$ref": "#/definitions/point2d" },
        "r_hip": { "$ref": "#/definitions/point2d" },
        "r_knee": { "$ref": "#/definitions/point2d" },
        "r_ankle": { "$ref": "#/definitions/point2d" },
        "l_hip": { "$ref": "#/definitions/point2d" },
        "l_knee": { "$ref": "#/definitions/point2d" },
        "l_ankle": { "$ref": "#/definitions/point2d" }
      }
    },
    "body_segments": {
      "type": "object",
      "description": "Semantic body segment descriptions",
      "properties": {
        "HEAD": { "type": "string" },
        "TORSO": { "type": "string" },
        "HIP": { "type": "string" },
        "LEGS": { "type": "string" },
        "HANDS": { "type": "string" }
      }
    },
    "camera_angle": { "type": "string" },
    "weight_distribution": { "type": "string" },
    "dynamic_modifier": { "type": "string" }
  },
  "definitions": {
    "point2d": {
      "type": "object",
      "properties": {
        "x": { "type": "number", "minimum": 0, "maximum": 1 },
        "y": { "type": "number", "minimum": 0, "maximum": 1 },
        "confidence": { "type": "number", "minimum": 0, "maximum": 1 }
      }
    }
  }
}

---

## SIUF 5 个标准骨架

### 1. SIUF_RUNWAY_WALK

{
  "pose_id": "SIUF_RUNWAY_WALK",
  "name_cn": "T台步态",
  "name_en": "Runway Walk",
  "keypoints": {
    "nose": { "x": 0.50, "y": 0.08, "confidence": 0.95 },
    "neck": { "x": 0.50, "y": 0.15, "confidence": 0.95 },
    "r_shoulder": { "x": 0.58, "y": 0.18, "confidence": 0.90 },
    "r_elbow": { "x": 0.62, "y": 0.28, "confidence": 0.85 },
    "r_wrist": { "x": 0.60, "y": 0.32, "confidence": 0.80 },
    "l_shoulder": { "x": 0.42, "y": 0.18, "confidence": 0.90 },
    "l_elbow": { "x": 0.38, "y": 0.28, "confidence": 0.85 },
    "l_wrist": { "x": 0.40, "y": 0.32, "confidence": 0.80 },
    "r_hip": { "x": 0.54, "y": 0.38, "confidence": 0.90 },
    "r_knee": { "x": 0.58, "y": 0.55, "confidence": 0.85 },
    "r_ankle": { "x": 0.60, "y": 0.72, "confidence": 0.80 },
    "l_hip": { "x": 0.46, "y": 0.38, "confidence": 0.90 },
    "l_knee": { "x": 0.42, "y": 0.55, "confidence": 0.85 },
    "l_ankle": { "x": 0.40, "y": 0.72, "confidence": 0.80 }
  },
  "body_segments": {
    "HEAD": "head_high gaze_forward chin_level",
    "TORSO": "torso_upright shoulders_back core_engaged",
    "HIP": "hip_sway weight_shifting pelvis_forward",
    "LEGS": "stride_forward toes_pointed heels_high",
    "HANDS": "arms_swinging_naturally"
  },
  "camera_angle": "front_low_angle",
  "weight_distribution": "even_shifting",
  "dynamic_modifier": "walking mid_stride"
}

### 2. SIUF_LOOKBACK_BEND

{
  "pose_id": "SIUF_LOOKBACK_BEND",
  "name_cn": "回头弯腰",
  "name_en": "Lookback Bend",
  "keypoints": {
    "nose": { "x": 0.55, "y": 0.12, "confidence": 0.95 },
    "neck": { "x": 0.52, "y": 0.18, "confidence": 0.95 },
    "r_shoulder": { "x": 0.60, "y": 0.22, "confidence": 0.90 },
    "r_elbow": { "x": 0.65, "y": 0.30, "confidence": 0.85 },
    "r_wrist": { "x": 0.62, "y": 0.38, "confidence": 0.80 },
    "l_shoulder": { "x": 0.44, "y": 0.20, "confidence": 0.90 },
    "l_elbow": { "x": 0.38, "y": 0.26, "confidence": 0.85 },
    "l_wrist": { "x": 0.35, "y": 0.32, "confidence": 0.80 },
    "r_hip": { "x": 0.56, "y": 0.36, "confidence": 0.90 },
    "r_knee": { "x": 0.62, "y": 0.52, "confidence": 0.85 },
    "r_ankle": { "x": 0.65, "y": 0.70, "confidence": 0.80 },
    "l_hip": { "x": 0.48, "y": 0.38, "confidence": 0.90 },
    "l_knee": { "x": 0.40, "y": 0.54, "confidence": 0.85 },
    "l_ankle": { "x": 0.38, "y": 0.72, "confidence": 0.80 }
  },
  "body_segments": {
    "HEAD": "head_turned_180deg gaze_camera chin_tilt_down",
    "TORSO": "torso_bent_forward twist_45deg lumbar_exaggerated",
    "HIP": "pelvis_tilt_back hip_pushed_back S_curve_maximized",
    "LEGS": "one_leg_forward weight_on_back_leg knee_bent",
    "HANDS": "one_hand_on_thigh other_near_face"
  },
  "camera_angle": "low_angle_side",
  "weight_distribution": "back_leg_heavy",
  "dynamic_modifier": "dynamic caught_mid_bend"
}

### 3. SIUF_POOLSIDE_RECLINE

{
  "pose_id": "SIUF_POOLSIDE_RECLINE",
  "name_cn": "泳池边侧卧",
  "name_en": "Poolside Recline",
  "keypoints": {
    "nose": { "x": 0.35, "y": 0.25, "confidence": 0.95 },
    "neck": { "x": 0.38, "y": 0.30, "confidence": 0.95 },
    "r_shoulder": { "x": 0.42, "y": 0.32, "confidence": 0.90 },
    "r_elbow": { "x": 0.38, "y": 0.28, "confidence": 0.85 },
    "r_wrist": { "x": 0.35, "y": 0.24, "confidence": 0.80 },
    "l_shoulder": { "x": 0.44, "y": 0.34, "confidence": 0.90 },
    "l_elbow": { "x": 0.50, "y": 0.38, "confidence": 0.85 },
    "l_wrist": { "x": 0.56, "y": 0.40, "confidence": 0.80 },
    "r_hip": { "x": 0.50, "y": 0.42, "confidence": 0.90 },
    "r_knee": { "x": 0.60, "y": 0.44, "confidence": 0.85 },
    "r_ankle": { "x": 0.70, "y": 0.45, "confidence": 0.80 },
    "l_hip": { "x": 0.52, "y": 0.44, "confidence": 0.90 },
    "l_knee": { "x": 0.65, "y": 0.46, "confidence": 0.85 },
    "l_ankle": { "x": 0.75, "y": 0.47, "confidence": 0.80 }
  },
  "body_segments": {
    "HEAD": "head_resting_on_hand gaze_soft chin_up",
    "TORSO": "torso_lateral_bend reclined_60deg",
    "HIP": "hip_pushed_out weight_on_side",
    "LEGS": "legs_extended crossed_at_ankle",
    "HANDS": "one_arm_supporting other_on_thigh"
  },
  "camera_angle": "low_angle_side",
  "weight_distribution": "side_weighted",
  "dynamic_modifier": "relaxed languid"
}

### 4. SIUF_EDITORIAL_STAND

{
  "pose_id": "SIUF_EDITORIAL_STAND",
  "name_cn": "杂志定点",
  "name_en": "Editorial Stand",
  "keypoints": {
    "nose": { "x": 0.48, "y": 0.10, "confidence": 0.95 },
    "neck": { "x": 0.50, "y": 0.16, "confidence": 0.95 },
    "r_shoulder": { "x": 0.58, "y": 0.20, "confidence": 0.90 },
    "r_elbow": { "x": 0.64, "y": 0.30, "confidence": 0.85 },
    "r_wrist": { "x": 0.60, "y": 0.36, "confidence": 0.80 },
    "l_shoulder": { "x": 0.42, "y": 0.20, "confidence": 0.90 },
    "l_elbow": { "x": 0.36, "y": 0.30, "confidence": 0.85 },
    "l_wrist": { "x": 0.34, "y": 0.36, "confidence": 0.80 },
    "r_hip": { "x": 0.55, "y": 0.40, "confidence": 0.90 },
    "r_knee": { "x": 0.56, "y": 0.58, "confidence": 0.85 },
    "r_ankle": { "x": 0.57, "y": 0.75, "confidence": 0.80 },
    "l_hip": { "x": 0.45, "y": 0.40, "confidence": 0.90 },
    "l_knee": { "x": 0.42, "y": 0.58, "confidence": 0.85 },
    "l_ankle": { "x": 0.40, "y": 0.75, "confidence": 0.80 }
  },
  "body_segments": {
    "HEAD": "head_neutral gaze_camera_intense jaw_defined",
    "TORSO": "torso_upright proud shoulders_back",
    "HIP": "contrapposto weight_on_back_leg",
    "LEGS": "contrapposto one_leg_straight one_relaxed",
    "HANDS": "one_hand_on_hip other_relaxed"
  },
  "camera_angle": "front_neutral",
  "weight_distribution": "contrapposto",
  "dynamic_modifier": "powerful editorial still"
}

### 5. SIUF_CANDID_MOTION

{
  "pose_id": "SIUF_CANDID_MOTION",
  "name_cn": "抓拍动态",
  "name_en": "Candid Motion",
  "keypoints": {
    "nose": { "x": 0.52, "y": 0.10, "confidence": 0.90 },
    "neck": { "x": 0.50, "y": 0.16, "confidence": 0.90 },
    "r_shoulder": { "x": 0.57, "y": 0.20, "confidence": 0.85 },
    "r_elbow": { "x": 0.60, "y": 0.15, "confidence": 0.80 },
    "r_wrist": { "x": 0.55, "y": 0.10, "confidence": 0.75 },
    "l_shoulder": { "x": 0.43, "y": 0.20, "confidence": 0.85 },
    "l_elbow": { "x": 0.40, "y": 0.28, "confidence": 0.80 },
    "l_wrist": { "x": 0.42, "y": 0.32, "confidence": 0.75 },
    "r_hip": { "x": 0.54, "y": 0.40, "confidence": 0.85 },
    "r_knee": { "x": 0.58, "y": 0.56, "confidence": 0.80 },
    "r_ankle": { "x": 0.60, "y": 0.72, "confidence": 0.75 },
    "l_hip": { "x": 0.46, "y": 0.40, "confidence": 0.85 },
    "l_knee": { "x": 0.42, "y": 0.56, "confidence": 0.80 },
    "l_ankle": { "x": 0.38, "y": 0.72, "confidence": 0.75 }
  },
  "body_segments": {
    "HEAD": "head_turned gaze_natural expression_spontaneous",
    "TORSO": "torso_natural_twist unposed",
    "HIP": "hip_natural_shift weight_in_motion",
    "LEGS": "mid_step natural_gait",
    "HANDS": "adjusting_hair touching_neck"
  },
  "camera_angle": "natural_eye_level",
  "weight_distribution": "mid_transfer",
  "dynamic_modifier": "candid spontaneous motion_blur"
}

---

## 骨架使用说明

### 与 ControlNet OpenPose 配合

1. 将 keypoints 转换为 OpenPose 格式的坐标（0-1 归一化 → 像素坐标）
2. 生成对应的骨架图片（黑底白线）
3. 作为 ControlNet OpenPose 的条件输入

### 在 Prompt 中引用

使用 body_segments 的语义描述，例如：
"参考SIUF_LOOKBACK_BEND骨架，HEAD: head_turned_180deg gaze_camera，TORSO: torso_bent_forward twist_45deg..."

### 坐标系说明

- x: 0.0=画面左边缘, 1.0=画面右边缘
- y: 0.0=画面顶部, 1.0=画面底部
- confidence: 0.0-1.0，表示该关键点的确定性
