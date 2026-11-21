/** Rahbar mark: a compass (rahbar = guide). Matches the app icon colours. */
export default function Logo({ size = 44 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
      <defs>
        <linearGradient id="rahbar-logo" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#6ee7b7" />
          <stop offset="1" stopColor="#047857" />
        </linearGradient>
      </defs>
      <rect width="48" height="48" rx="14" fill="url(#rahbar-logo)" />
      <circle cx="24" cy="24" r="13" fill="none" stroke="#fff" strokeWidth="2.5" />
      <path d="M24 11.5 L28.2 24 L24 36.5 L19.8 24 Z" fill="#fde68a" />
      <circle cx="24" cy="24" r="2.6" fill="#fff" />
    </svg>
  );
}