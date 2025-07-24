export type drawingType = "zone" | "line";

export interface ArrowType {
  id: string;
  points: number[];
}

export interface Rectangle {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}
