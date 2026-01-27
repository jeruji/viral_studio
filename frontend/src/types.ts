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
