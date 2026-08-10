import * as React from 'react';

const noopSubscribe = () => () => {};

/**
 * False while server-rendering, true once hydrated on the client.
 *
 * The usual `useState(false)` + `useEffect(() => setState(true))` does the same
 * job but sets state inside an effect, which forces a second render on every
 * mount — the React Compiler lint rule rejects it. `useSyncExternalStore` gets
 * there with a server snapshot instead of a render pass.
 */
export function useHydrated(): boolean {
  return React.useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );
}
