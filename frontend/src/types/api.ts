/**
 * Mirrors the FastAPI backend's Pydantic schemas exactly (see
 * backend/app/schemas/*.py and backend/app/models/*.py). Keep in sync
 * by hand -- there's no shared codegen between the two right now.
 */

export type SourcePlatform = "instagram" | "youtube" | "other";

export type ProjectStatus =
  | "pending"
  | "downloading"
  | "analyzing"
  | "blueprint_ready"
  | "awaiting_assets"
  | "matching"
  | "rendering"
  | "completed"
  | "failed";

export type BlueprintStatus = "pending" | "processing" | "completed" | "failed";

export type SlotType = "video_clip" | "photo" | "text_overlay" | "motion_graphic";

export type SlotOrientation = "portrait" | "landscape" | "square" | "any";

export type AssetType = "photo" | "video";

export type UploadStatus = "uploading" | "processing" | "ready" | "failed";

export type RenderJobStatus = "queued" | "processing" | "completed" | "failed";

export interface UserOut {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  subscription_tier: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface ProjectOut {
  id: string;
  title: string;
  source_url: string;
  source_platform: SourcePlatform;
  status: ProjectStatus;
  error_message: string | null;
  created_at: string;
}

export interface SceneCamera {
  movement_type: string;
  confidence: number;
  magnitude: number;
}

export interface SceneBeatAlignment {
  nearest_beat_time_seconds: number | null;
  offset_seconds: number | null;
  is_on_beat: boolean;
}

export interface SceneTextOverlay {
  text: string;
  start_time_seconds: number;
  end_time_seconds: number;
}

export interface EditBlueprintScene {
  scene_index: number;
  start_time_seconds: number;
  end_time_seconds: number;
  duration_seconds: number;
  camera_movement: SceneCamera;
  beat_alignment: SceneBeatAlignment;
  text_overlays: SceneTextOverlay[];
}

export interface EditBlueprint {
  video: { duration_seconds: number | null; fps: number | null; resolution: { width: number | null; height: number | null } };
  audio_profile: { has_audio: boolean; bpm: number | null; beat_count: number; beat_times_seconds: number[] };
  scenes: EditBlueprintScene[];
  scene_count: number;
  generated_at: string;
}

export interface BlueprintOut {
  id: string;
  project_id: string;
  status: BlueprintStatus;
  source_video_s3_key: string | null;
  source_duration_seconds: number | null;
  fps: number | null;
  resolution_width: number | null;
  resolution_height: number | null;
  scene_cuts: { cuts: unknown[]; cut_count: number } | null;
  beat_map: { has_audio: boolean; bpm: number | null; beat_times_seconds: number[]; beat_count?: number } | null;
  transitions: unknown | null;
  camera_movements: unknown | null;
  color_grading_profile: unknown | null;
  audio_stem_s3_keys: unknown | null;
  transcript: unknown | null;
  text_overlays: { overlays: SceneTextOverlay[]; overlay_count: number } | null;
  edit_blueprint: EditBlueprint | null;
  created_at: string;
}

export interface AssetSlotOut {
  id: string;
  slot_index: number;
  start_time_seconds: number;
  end_time_seconds: number;
  duration_seconds: number;
  slot_type: SlotType;
  required_orientation: SlotOrientation;
  camera_movement_type: string | null;
  description: string | null;
  matched_asset_id: string | null;
  match_confidence: number | null;
  is_manual: boolean;
  gap_fill_s3_key: string | null;
}

export interface UserAssetOut {
  id: string;
  asset_type: AssetType;
  upload_status: UploadStatus;
  s3_key: string;
  file_size_bytes: number | null;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  has_face: boolean | null;
  face_count: number | null;
  created_at: string;
}

export interface PresignUploadResponse {
  asset_id: string;
  upload_url: string;
  s3_key: string;
  expires_in: number;
}

export interface ConfirmUploadResponse {
  asset_id: string;
  upload_status: UploadStatus;
  file_size_bytes: number | null;
}

export interface RenderJobOut {
  id: string;
  status: RenderJobStatus;
  progress_percent: number;
  output_s3_key: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface MediaUrlOut {
  url: string;
  expires_in: number;
}
