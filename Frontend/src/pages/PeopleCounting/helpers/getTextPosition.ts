export function getTextPosition(
  points: number[],
  offset: number
): [number, number] {
  // Calculate the angle of the line
  const angle = Math.atan2(points[3] - points[1], points[2] - points[0]);

  // Midpoint of the line
  const midX = (points[0] + points[2]) / 2;
  const midY = (points[1] + points[3]) / 2;

  // Offset for text above the line
  const textX = midX + (offset * Math.sin(angle)) / 2;
  const textY = midY - (offset * Math.cos(angle)) / 2;

  return [textX, textY];
}
