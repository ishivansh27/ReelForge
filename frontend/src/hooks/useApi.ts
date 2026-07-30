import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  AssetSlotOut,
  BlueprintOut,
  ConfirmUploadResponse,
  MediaUrlOut,
  PresignUploadResponse,
  ProjectOut,
  RenderJobOut,
  UserAssetOut,
} from "@/types/api";

// Statuses where the backend pipeline is actively chaining Celery
// tasks in the background -- the UI should keep polling until it
// lands on a stable status (blueprint_ready, awaiting_assets, failed, etc.)
const IN_PROGRESS_PROJECT_STATUSES = new Set(["pending", "downloading", "analyzing", "blueprint_ready"]);
const POLL_INTERVAL_MS = 2500;

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: async () => (await api.get<ProjectOut[]>("/projects")).data,
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: async () => (await api.get<ProjectOut>(`/projects/${projectId}`)).data,
    enabled: !!projectId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && IN_PROGRESS_PROJECT_STATUSES.has(status) ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (sourceUrl: string) =>
      (await api.post<ProjectOut>("/projects", { source_url: sourceUrl })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useBlueprint(projectId: string | undefined, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["blueprint", projectId],
    queryFn: async () => (await api.get<BlueprintOut>(`/projects/${projectId}/blueprint`)).data,
    enabled: !!projectId && (options?.enabled ?? true),
    retry: false,
    refetchInterval: (query) => (query.state.data?.status === "processing" ? POLL_INTERVAL_MS : false),
  });
}

export function useAssetSlots(projectId: string | undefined, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["asset-slots", projectId],
    queryFn: async () => (await api.get<AssetSlotOut[]>(`/projects/${projectId}/asset-requirements`)).data,
    enabled: !!projectId && (options?.enabled ?? true),
    retry: 3,
    retryDelay: 1500,
    // generate_asset_slots runs as a follow-on task right after the
    // blueprint completes -- there's a brief window where the project
    // is already "awaiting_assets" but the slot rows haven't landed
    // yet, so a 404 here is expected transiently. Cap it: if slots are
    // still empty after ~15s of polling, stop -- otherwise a project
    // that failed before ever reaching that stage polls this 404
    // forever (asset_slots will never exist if the blueprint never did).
    refetchInterval: (query) => {
      const empty = !query.state.data || query.state.data.length === 0;
      const pollingTooLong = query.state.dataUpdateCount + query.state.errorUpdateCount > 6;
      return empty && !pollingTooLong ? 2500 : false;
    },
  });
}

export function useProjectAssets(projectId: string | undefined) {
  return useQuery({
    queryKey: ["project-assets", projectId],
    queryFn: async () => (await api.get<UserAssetOut[]>(`/projects/${projectId}/assets`)).data,
    enabled: !!projectId,
  });
}

export function usePresignUpload(projectId: string) {
  return useMutation({
    mutationFn: async (file: { filename: string; contentType: string; assetType: "photo" | "video" }) =>
      (
        await api.post<PresignUploadResponse>("/uploads/presign", {
          project_id: projectId,
          filename: file.filename,
          content_type: file.contentType,
          asset_type: file.assetType,
        })
      ).data,
  });
}

export function useConfirmUpload() {
  return useMutation({
    mutationFn: async (assetId: string) =>
      (await api.post<ConfirmUploadResponse>(`/uploads/${assetId}/confirm`)).data,
  });
}

export function useUploadAsset(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const assetType: "photo" | "video" = file.type.startsWith("video/") ? "video" : "photo";
      const presigned = (
        await api.post<PresignUploadResponse>("/uploads/presign", {
          project_id: projectId,
          filename: file.name,
          content_type: file.type,
          asset_type: assetType,
        })
      ).data;

      // Direct-to-S3 PUT -- deliberately a plain, unauthenticated
      // fetch (not the `api` axios instance), since a presigned URL
      // already carries its own auth via query-string signature and
      // must NOT be sent our JWT Authorization header.
      await fetch(presigned.upload_url, {
        method: "PUT",
        headers: { "Content-Type": file.type },
        body: file,
      });

      return (await api.post<ConfirmUploadResponse>(`/uploads/${presigned.asset_id}/confirm`)).data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["project-assets", projectId] }),
  });
}

export function useTriggerMatchAssets(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post(`/projects/${projectId}/match-assets`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["asset-slots", projectId] });
    },
  });
}

export function useOverrideAssetSlot(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ slotId, assetId }: { slotId: string; assetId: string | null }) =>
      (
        await api.patch<AssetSlotOut>(`/projects/${projectId}/asset-requirements/${slotId}`, {
          asset_id: assetId,
        })
      ).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["asset-slots", projectId] }),
  });
}

export function useTriggerGapFill(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post(`/projects/${projectId}/generate-gap-fills`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["asset-slots", projectId] }),
  });
}

export function useTriggerRender(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => (await api.post<RenderJobOut>(`/projects/${projectId}/render`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["render-jobs", projectId] }),
  });
}

export function useRenderJobs(projectId: string | undefined) {
  return useQuery({
    queryKey: ["render-jobs", projectId],
    queryFn: async () => (await api.get<RenderJobOut[]>(`/projects/${projectId}/render-jobs`)).data,
    enabled: !!projectId,
    refetchInterval: (query) => {
      const jobs = query.state.data;
      const active = jobs?.some((j) => j.status === "queued" || j.status === "processing");
      return active ? POLL_INTERVAL_MS : false;
    },
  });
}

export function useAssetUrl(projectId: string | undefined, assetId: string | undefined) {
  return useQuery({
    queryKey: ["asset-url", projectId, assetId],
    queryFn: async () => (await api.get<MediaUrlOut>(`/projects/${projectId}/assets/${assetId}/url`)).data,
    enabled: !!projectId && !!assetId,
    staleTime: 5 * 60_000,
  });
}

export function useGapFillUrl(projectId: string | undefined, slotId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["gap-fill-url", projectId, slotId],
    queryFn: async () =>
      (await api.get<MediaUrlOut>(`/projects/${projectId}/asset-requirements/${slotId}/gap-fill-url`)).data,
    enabled: !!projectId && !!slotId && enabled,
    staleTime: 5 * 60_000,
  });
}

export function useReferenceVideoUrl(projectId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["reference-video-url", projectId],
    queryFn: async () => (await api.get<MediaUrlOut>(`/projects/${projectId}/reference-video-url`)).data,
    enabled: !!projectId && enabled,
    retry: false,
    staleTime: 5 * 60_000,
  });
}

export function useRenderDownloadUrl(projectId: string | undefined, jobId: string | undefined) {
  return useQuery({
    queryKey: ["render-download-url", projectId, jobId],
    queryFn: async () =>
      (await api.get<MediaUrlOut>(`/projects/${projectId}/render-jobs/${jobId}/download-url`)).data,
    enabled: !!projectId && !!jobId,
    staleTime: 5 * 60_000,
  });
}
