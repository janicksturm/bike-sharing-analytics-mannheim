import { useState, useEffect } from "react";

const useFetch = <T,>(url: string) => {
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    fetch(url)
      .then((res) => res.json())
      .then((data) => setData(data));
  }, [url]);

  return [data] as const;
};

export default useFetch;