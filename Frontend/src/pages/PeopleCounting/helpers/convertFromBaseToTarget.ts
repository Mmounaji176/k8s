export const convertFromBaseToTarget = (
  baseImageWith: number,
  baseImageHeight: number,
  targetImageWith: number,
  targetImageHeight: number,
  baseImageX: number,
  baseImageY: number
) => {
  const x = (baseImageX / baseImageWith) * targetImageWith;

  const y = (baseImageY / baseImageHeight) * targetImageHeight;

  return { x, y };
};
