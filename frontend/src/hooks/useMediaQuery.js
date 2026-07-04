import { useEffect, useState } from 'react';

// Reactively track a CSS media query, e.g. useMediaQuery('(max-width: 640px)').
export default function useMediaQuery(query) {
  const [matches, setMatches] = useState(
    () => typeof window !== 'undefined' && !!window.matchMedia && window.matchMedia(query).matches
  );

  useEffect(() => {
    if (!window.matchMedia) return undefined;
    const mediaQuery = window.matchMedia(query);
    const onChange = (event) => setMatches(event.matches);
    setMatches(mediaQuery.matches);
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', onChange);
      return () => mediaQuery.removeEventListener('change', onChange);
    }
    mediaQuery.addListener(onChange);
    return () => mediaQuery.removeListener(onChange);
  }, [query]);

  return matches;
}
