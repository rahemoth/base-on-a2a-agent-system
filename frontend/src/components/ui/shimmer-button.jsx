export function ShimmerButton({
  shimmerColor = "#ffffff",
  shimmerSize = "0.05em",
  shimmerDuration = "3s",
  borderRadius = "100px",
  background = "rgba(0, 0, 0, 1)",
  className = "",
  children,
  onClick,
  type = "button",
  ...props
}) {
  return (
    <button
      type={type}
      style={{
        "--shimmer-color": shimmerColor,
        "--shimmer-size": shimmerSize,
        "--shimmer-duration": shimmerDuration,
        "--border-radius": borderRadius,
        "--background": background,
        borderRadius,
      }}
      className={`group relative z-0 flex cursor-pointer items-center justify-center overflow-hidden whitespace-nowrap border border-white/10 px-6 py-3 text-white [background:var(--background)] [border-radius:var(--border-radius)] transform-gpu transition-transform duration-300 ease-in-out active:translate-y-[1px] ${className}`}
      onClick={onClick}
      {...props}
    >
      <span className="relative z-10">{children}</span>
    </button>
  );
}
