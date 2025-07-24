import { Button, Card, CardFooter, CardHeader } from "@nextui-org/react";
import { RiDeleteBin6Fill } from "react-icons/ri";

export function StreamCard(image: any) {
  return (
    <Card isFooterBlurred className="w-full sm:w-[17.5rem] group h-64">
      <CardHeader className="hidden group-hover:flex absolute z-10 top-1 justify-end">
        <Button
          variant="light"
          color="danger"
          className="text-primary-foreground hover:text-danger-200"
          isIconOnly
        >
          <RiDeleteBin6Fill className="w-4 h-4" />
        </Button>
      </CardHeader>
      <img
        alt="NextUI hero Image"
        src={`${import.meta.env.VITE_APP_BACKEND}${image.image.thumbnail}`}
        className="z-0 w-full h-full object-cover object-center"
      />
      <CardFooter className="absolute bg-black/40 bottom-0 z-10 border-t-1 border-default-600 dark:border-default-100">
        <div className="flex flex-grow gap-2 items-center">
          <div className="flex flex-col">
            <p className="text-tiny text-white/60">
              Camera {image.image.title}
            </p>
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}
