import { useCallback, useEffect, useRef, useState, type SetStateAction } from "react";

/**
 * `useState` plus `setIfMounted`, which drops an answer that arrives after the
 * component is gone. StrictMode unmounts and remounts once in dev, so the
 * flag is reset on every mount. Call it before the effect that starts loading.
 */
export function useMountedState<S>(initial: S) {
  const [state, setState] = useState<S>(initial);
  const mounted = useRef(false);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const setIfMounted = useCallback((next: SetStateAction<S>) => {
    if (mounted.current) setState(next);
  }, []);

  return [state, setState, setIfMounted] as const;
}
