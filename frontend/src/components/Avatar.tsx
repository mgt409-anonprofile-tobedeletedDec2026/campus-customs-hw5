import type { Character } from "../characters";

// A small cartoon portrait drawn in SVG from each character's look.
export function Avatar({ who, size = 56 }: { who: Character; size?: number }) {
  const { look } = who;
  return (
    <svg className="avatar" width={size} height={size} viewBox="0 0 64 64" role="img" aria-label={`${who.name} portrait`}>
      <circle cx="32" cy="32" r="31" fill={who.soft} stroke={who.color} strokeWidth="2" />
      {look.hairStyle === "curly" && <ellipse cx="32" cy="30" rx="19" ry="20" fill={look.hair} />}
      {/* shoulders */}
      <path d="M8 64 C10 48 20 44 32 44 C44 44 54 48 56 64 Z" fill={look.shirt} />
      <path d="M25 44 L32 53 L39 44 Z" fill={look.collar} />
      {look.tie && <path d="M30.5 47 L33.5 47 L35 60 L32 63 L29 60 Z" fill={look.tie} />}
      <rect x="28" y="36" width="8" height="9" rx="3" fill={look.skin} />
      {/* head */}
      <ellipse cx="32" cy="27" rx="12" ry="14" fill={look.skin} />
      {look.hairStyle === "side" && <path d="M19 25 C19 12 30 9 38 11 C44 12 46 18 45 24 C40 18 30 17 24 20 C22 21 20 23 19 25 Z" fill={look.hair} />}
      {look.hairStyle === "bowl" && <path d="M19 26 C18 13 26 10 32 10 C38 10 46 13 45 26 C42 21 36 19 32 21 C28 19 22 21 19 26 Z" fill={look.hair} />}
      {look.hairStyle === "short" && <path d="M20 22 C21 13 28 11 33 11 C40 11 45 15 44 23 C40 18 26 17 20 22 Z" fill={look.hair} />}
      {look.hairStyle === "buzz" && <path d="M21 20 C23 14 28 12 32 12 C37 12 42 14 43 20 C38 17 26 17 21 20 Z" fill={look.hair} />}
      {look.hairStyle === "curly" && <path d="M20 24 C20 14 27 10 33 11 C40 11 45 16 44 25 C40 18 30 16 25 19 C23 20 21 22 20 24 Z" fill={look.hair} />}
      {look.hairStyle === "silver" && <path d="M20 23 C20 13 28 11 33 11 C41 11 45 15 44 23 C41 19 36 17 32 18 C27 17 22 19 20 23 Z" fill={look.hair} />}
      {/* face */}
      <circle cx="27" cy="27" r="1.6" fill="#1e2a4a" />
      <circle cx="37" cy="27" r="1.6" fill="#1e2a4a" />
      {look.glasses && (
        <g fill="none" stroke="#3b2a20" strokeWidth="1.6">
          <rect x="22.5" y="23.5" width="9" height="7" rx="1.5" />
          <rect x="32.5" y="23.5" width="9" height="7" rx="1.5" />
          <path d="M31.5 26.5 L32.5 26.5" />
        </g>
      )}
      {look.beard === "goatee" && <path d="M28 35 C29 39 35 39 36 35 C34 36.5 30 36.5 28 35 Z" fill={look.hair} />}
      {look.beard === "mustache" && <path d="M27 33 C30 31 34 31 37 33 C34 32.5 30 32.5 27 33 Z" fill={look.hair} />}
      <path d="M28 34 Q32 37 36 34" fill="none" stroke="#7a3b2e" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}
