import { useRef, useState, useCallback } from "react";
import { Button } from "@nextui-org/button";
import { Layer, Rect, Stage, Image } from "react-konva";
import { v1 as uuidv4 } from "uuid";
import Konva from "konva";
import { IoMoveSharp } from "react-icons/io5";
import { Rectangle } from "../types/peopleCountingTypes";
import useImage from "use-image";

export default function ZoneSelecter({ imageUrl } : { imageUrl: string }) {
  const [image] = useImage(
    "https://c8.alamy.com/comp/FCYX91/customers-serve-themselves-queue-to-pay-la-place-self-service-food-FCYX91.jpg"
  );
  const imageContainer = useRef<HTMLDivElement | null>(null);
  const stageRef = useRef<Konva.Stage>(null);
  const [rectangles, setRectangles] = useState<Rectangle[]>([]);
  const currentRectId = useRef("");
  const isPaiting = useRef(false);
  const [isDragable, setIsDragable] = useState(false);

  //* drawind rectangle depending on the mouse position with the help of the stage
  const onPointerDown = useCallback(() => {
    if (isDragable) return;
    isPaiting.current = true;
    const { x, y } = stageRef.current?.getPointerPosition() || { x: 0, y: 0 };
    const id = uuidv4();

    currentRectId.current = id;

    setRectangles((prev) => [...prev, { id, x, y, width: 20, height: 20 }]);
  }, [isDragable]);

  //* drawing the rectangle while the mouse is moving
  const onPointerMove = useCallback(() => {
    if (!isPaiting.current) return;
    const { x, y } = stageRef.current?.getPointerPosition() || { x: 0, y: 0 };

    setRectangles((prev) =>
      prev.map((rect) => {
        if (rect.id === currentRectId.current) {
          return {
            ...rect,
            width: x - rect.x,
            height: y - rect.y,
          };
        }

        return rect;
      })
    );
  }, [isPaiting, currentRectId]);

  //* stop drawing the rectangle when the mouse is up
  const onPointerUp = useCallback(() => {
    rectangles.forEach((rect, index) => {
      console.log(
        `rect ${index}: point one {x: ${rect.x}, y: ${rect.y}}, point two {x: ${
          rect.x + rect.width
        }, y: ${rect.y + rect.height}}`
      );
    });
    isPaiting.current = false;
  }, [rectangles]);

  return (
    <div
      className="image-container w-full h-full relative"
      ref={imageContainer}
    >
      <Button
        className="w-12 absolute top-2 right-2 z-50"
        onClick={() => setRectangles([])}
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
            image={image}
            width={imageContainer.current?.clientWidth}
            height={imageContainer.current?.clientHeight}
          />
          <Rect
            width={imageContainer.current?.clientWidth}
            height={imageContainer.current?.clientHeight}
          />
          {rectangles.map((rect) => (
            <Rect
              key={rect.id}
              x={rect.x}
              y={rect.y}
              width={rect.width}
              height={rect.height}
              strokeWidth={2}
              stroke={"yellow"}
              draggable={isDragable}
            />
          ))}
        </Layer>
      </Stage>
    </div>
  );
}
