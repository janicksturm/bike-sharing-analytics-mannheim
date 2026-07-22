import { useState, useEffect, useCallback, useRef } from "react";

interface UseFetchResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

/**
 * Generic data-fetching hook with loading/error states and optional
 * auto-refresh via `refetchIntervalMs`.
 */
function useFetch<T>(url: string, refetchIntervalMs?: number): UseFetchResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        return res.json();
      })
      .then((json: T) => {
        setData(json);
        setError(null);
      })
      .catch((err: Error) => {
        setError(err.message ?? "Fetch failed");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [url]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Optional polling interval
  useEffect(() => {
    if (!refetchIntervalMs || refetchIntervalMs <= 0) return;

    intervalRef.current = setInterval(fetchData, refetchIntervalMs);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchData, refetchIntervalMs]);

  return { data, loading, error, refetch: fetchData };
}

export default useFetch;