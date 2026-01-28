export type Job = {
  id: number;
  status: string;
  params_json?: string | null;
  inputs_json?: string | null;
  log_path?: string | null;
  report_path?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
};

export const moodOptions = ["happy", "hype", "sad", "mellow", "nostalgic"];
export const audioStyles = ["jedag_jedug", "tiktok_house", "mellow_rainy", "cinematic_epic", "lofi_chill"];
export const platformOptions = ["tiktok","instagram", "youtube_short","youtube_video"];
