import * as React from "react"

const MOBILE_BREAKPOINT = 768
const QUERY = `(max-width: ${MOBILE_BREAKPOINT - 1}px)`

/**
 * Is the viewport phone-sized? Used by the sidebar to switch to a drawer.
 *
 * shadcn generates this with `useState` + `useEffect`, which the React Compiler
 * lint rule rejects: setting state synchronously inside an effect causes a
 * cascading re-render on every mount. A media query is an external store, so
 * `useSyncExternalStore` is the primitive built for it — it subscribes without
 * an extra render pass and takes an explicit server snapshot, which keeps SSR
 * and hydration agreeing.
 */
export function useIsMobile(): boolean {
  const subscribe = React.useCallback((onChange: () => void) => {
    const mql = window.matchMedia(QUERY)
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return React.useSyncExternalStore(
    subscribe,
    () => window.matchMedia(QUERY).matches,
    // The server has no viewport; assume desktop so the sidebar renders expanded.
    () => false,
  )
}
