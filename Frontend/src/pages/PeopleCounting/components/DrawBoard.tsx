import { useRef, useCallback, Fragment, useEffect, useState } from "react";
import { Button } from "@nextui-org/button";
import { Layer, Rect, Stage, Image, Line, Text } from "react-konva";
import { v1 as uuidv4 } from "uuid";
import Konva from "konva";
import { IoMoveSharp } from "react-icons/io5";
import { ArrowType, drawingType, Rectangle } from "../types/peopleCountingTypes";
import useImage from "use-image";
import { getTextPosition } from "../helpers/getTextPosition";
import { create } from "zustand";
import { Spinner } from "@nextui-org/react";

// Arrow store (unchanged)
type ArrowActions = {
  addArrow: (arrow: ArrowType) => void;
  updateArrowPoints: (id: string, points: number[]) => void;
  resetArrows: () => void;
};

export const useArrowsStore = create<{
  arrows: ArrowType[];
} & ArrowActions>((set) => ({
  arrows: [],
  addArrow: (arrow) =>
    set((state) => ({
      arrows: [...state.arrows, arrow],
    })),
  updateArrowPoints: (id, points) =>
    set((state) => ({
      arrows: state.arrows.map((arrow) =>
        arrow.id === id ? { ...arrow, points } : arrow
      ),
    })),
  resetArrows: () => set({ arrows: [] }),
}));

// New Rectangle store
type RectangleActions = {
  addRectangle: (rectangle: Rectangle) => void;
  updateRectangle: (id: string, updates: Partial<Rectangle>) => void;
  resetRectangles: () => void;
};

export const useRectanglesStore = create<{
  rectangles: Rectangle[];
} & RectangleActions>((set) => ({
  rectangles: [],
  addRectangle: (rectangle) =>
    set((state) => ({
      rectangles: [...state.rectangles, rectangle],
    })),
  updateRectangle: (id, updates) =>
    set((state) => ({
      rectangles: state.rectangles.map((rect) =>
        rect.id === id ? { ...rect, ...updates } : rect
      ),
    })),
  resetRectangles: () => set({ rectangles: [] }),
}));

export default function DrawBoard({
  imageUrl,
  type,
}: {
  imageUrl: string;
  type: drawingType;
}) {
  const [image] = useImage(imageUrl);
  const imageContainer = useRef<HTMLDivElement | null>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const currentRectId = useRef("");
  const isPaiting = useRef(false);
  const [isDragable, setIsDragable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const arrowStore = useArrowsStore();
  const rectangleStore = useRectanglesStore();

  useEffect(() => {
    if (!image) {
      setLoading(true);
    } else {
      setLoading(false);
      // Store the original image dimensions
      setImageSize({
        width: image.naturalWidth,
        height: image.naturalHeight
      });
    }
    return () => {
      setLoading(true);
      image && URL.revokeObjectURL(image.src);
      image?.remove();
    };
  }, [image]);

  // Convert stage coordinates to original image coordinates
  const stageToImageCoords = useCallback(
    (stageX: number, stageY: number) => {
      if (!imageContainer.current || !image) return { x: stageX, y: stageY };

      const containerWidth = imageContainer.current.clientWidth;
      const containerHeight = imageContainer.current.clientHeight;

      // Calculate scaling factors
      const scaleX = imageSize.width / containerWidth;
      const scaleY = imageSize.height / containerHeight;

      // Convert coordinates
      const imageX = Math.round(stageX * scaleX);
      const imageY = Math.round(stageY * scaleY);

      return { x: imageX, y: imageY };
    },
    [image, imageSize]
  );

  // Convert image coordinates to stage coordinates
  const imageToStageCoords = useCallback(
    (imageX: number, imageY: number) => {
      if (!imageContainer.current || !image) return { x: imageX, y: imageY };

      const containerWidth = imageContainer.current.clientWidth;
      const containerHeight = imageContainer.current.clientHeight;

      // Calculate scaling factors
      const scaleX = containerWidth / imageSize.width;
      const scaleY = containerHeight / imageSize.height;

      // Convert coordinates
      const stageX = imageX * scaleX;
      const stageY = imageY * scaleY;

      return { x: stageX, y: stageY };
    },
    [image, imageSize]
  );

  const onPointerDown = useCallback(() => {
    if (isDragable) return;
    isPaiting.current = true;
    const { x: stageX, y: stageY } = stageRef.current?.getPointerPosition() || { x: 0, y: 0 };
    const { x, y } = stageToImageCoords(stageX, stageY);
    const id = uuidv4();

    currentRectId.current = id;

    if (type === "zone") {
      // Store original image coordinates in the data model
      rectangleStore.addRectangle({ id, x, y, width: 20, height: 20 });
    } else {
      arrowStore.addArrow({ id, points: [x, y, x + 20, y + 20] });
    }
  }, [isDragable, type, arrowStore, rectangleStore, stageToImageCoords]);

  const onPointerMove = useCallback(() => {
    if (!isPaiting.current) return;
    const { x: stageX, y: stageY } = stageRef.current?.getPointerPosition() || { x: 0, y: 0 };
    const { x, y } = stageToImageCoords(stageX, stageY);

    if (type === "zone") {
      const currentRect = rectangleStore.rectangles.find(rect => rect.id === currentRectId.current);
      if (currentRect) {
        rectangleStore.updateRectangle(currentRectId.current, {
          width: x - currentRect.x,
          height: y - currentRect.y,
        });
      }
    } else {
      const currentArrow = arrowStore.arrows.find(arrow => arrow.id === currentRectId.current);
      if (currentArrow) {
        arrowStore.updateArrowPoints(currentRectId.current, [
          currentArrow.points[0],
          currentArrow.points[1],
          x,
          y,
        ]);
      }
    }
  }, [isPaiting, currentRectId, type, arrowStore, rectangleStore, stageToImageCoords]);

  const onPointerUp = useCallback(() => {
    rectangleStore.rectangles.forEach((rect, index) => {
      console.log(
        `rect ${index}: point one {x: ${rect.x}, y: ${rect.y}}, point two {x: ${rect.x + rect.width}, y: ${rect.y + rect.height}} (in original image coordinates)`
      );
    });
    isPaiting.current = false;
  }, [rectangleStore.rectangles]);

  // Render rectangles and arrows in stage coordinates
  const renderRects = useCallback(() => {
    return rectangleStore.rectangles.map(rect => {
      // Convert from image coordinates to stage coordinates for display
      const stageStart = imageToStageCoords(rect.x, rect.y);
      const stageEnd = imageToStageCoords(rect.x + rect.width, rect.y + rect.height);

      return (
        <Rect
          key={rect.id}
          x={stageStart.x}
          y={stageStart.y}
          width={stageEnd.x - stageStart.x}
          height={stageEnd.y - stageStart.y}
          strokeWidth={2}
          stroke={"yellow"}
          draggable={isDragable}
          onDragEnd={(e) => {
            if (isDragable) {
              // When dragged, update with new image coordinates
              const { x: stageX, y: stageY } = e.target.position();
              const { x, y } = stageToImageCoords(stageX, stageY);
              rectangleStore.updateRectangle(rect.id, { x, y });
            }
          }}
        />
      );
    });
  }, [rectangleStore.rectangles, isDragable, imageToStageCoords, stageToImageCoords]);

  const renderArrows = useCallback(() => {
    return arrowStore.arrows.map((arrow) => {
      // Convert points from image coordinates to stage coordinates
      const stagePoints = [
        imageToStageCoords(arrow.points[0], arrow.points[1]),
        imageToStageCoords(arrow.points[2], arrow.points[3])
      ];

      const pointsArray = [
        stagePoints[0].x, stagePoints[0].y,
        stagePoints[1].x, stagePoints[1].y
      ];

      const [x1, y1] = getTextPosition(pointsArray, 100);
      const [x2, y2] = getTextPosition(pointsArray, -100);

      return (
        <Fragment key={uuidv4()}>
          <Text
            x={x1}
            y={y1}
            text="In"
            fill={"yellow"}
            fontSize={40}
          />
          <Text
            x={x2}
            y={y2}
            text="Out"
            fill={"yellow"}
            fontSize={40}
          />
          <Line
            key={uuidv4()}
            points={pointsArray}
            fill={"yellow"}
            stroke={"yellow"}
            strokeWidth={5}
            draggable={isDragable}
            onDragEnd={(e) => {
              if (isDragable) {
                // Update arrow position in image coordinates when dragged
                // This is more complex and would need additional handling
              }
            }}
          />
        </Fragment>
      );
    });
  }, [arrowStore.arrows, isDragable, imageToStageCoords]);

  return (
    <div className="image-container w-full h-full relative" ref={imageContainer}>
      <Button
        className="w-12 absolute top-2 right-2 z-50"
        onClick={() => {
          rectangleStore.resetRectangles();
          arrowStore.resetArrows();
        }}
      >
        Reset
      </Button>

      <Button
        className="w-12 absolute top-14 right-2 z-50"
        color={isDragable ? "success" : "default"}
        onClick={() => {
          setIsDragable((prev) => !prev);
          isPaiting.current = false;
        }}
      >
        <IoMoveSharp size={30} />
      </Button>

      {loading && (
        <div className="absolute inset-0 flex justify-center items-center z-40">
          <Spinner size="large" />
        </div>
      )}

      {!loading && (
        <Stage
          width={imageContainer.current?.clientWidth}
          height={imageContainer.current?.clientHeight}
          onPointerDown={onPointerDown}
          onPointerUp={onPointerUp}
          onPointerMove={onPointerMove}
          ref={stageRef}
        >
          <Layer>
            <Image
              id="stream-image"
              image={image}
              width={imageContainer.current?.clientWidth}
              height={imageContainer.current?.clientHeight}
            />
            <Rect
              width={imageContainer.current?.clientWidth}
              height={imageContainer.current?.clientHeight}
            />
            {type === "zone" ? renderRects() : renderArrows()}
          </Layer>
        </Stage>
      )}

      {!loading && (
        <div className="absolute bottom-2 left-2 bg-black/50 text-white p-2 rounded">
          Image Resolution: {imageSize.width}x{imageSize.height}
        </div>
      )}
    </div>
  );
}