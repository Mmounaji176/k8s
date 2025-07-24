import {
  Card,
  CardHeader,
  CardFooter,
  Image,
  Button,
  CardBody,
} from "@nextui-org/react";
import { IconType } from "react-icons";
import { useNavigate } from "react-router-dom";

export interface FeatureCardProps {
  title: string;
  description: string;
  thumbnailUrl: string;
  FooterIcon: IconType;
  footerDescription: string;
  buttonText: string;
  navLink: string;
  className?: string;
}

export default function FeatureCard({
  title,
  description,
  thumbnailUrl,
  FooterIcon,
  footerDescription,
  buttonText,
  navLink,
  ...props
}: FeatureCardProps) {
  const navigate = useNavigate();

  const isActive = buttonText.includes("Start");

  return (
    <div {...props}>
      <Card className="flex flex-col items-center justify-center w-96 h-[26.2rem] col-span-12 sm:col-span-7 bg-[#2F3241]/50">
        <CardBody className="flex flex-col gap-4">
          <Image className="w-full h-auto object-scale-down " src={thumbnailUrl} />
          <div className="flex flex-col gap-2">
            <h1 className="text-2xl font-bold">{title}</h1>
            <p>{description}</p>
          </div>
        </CardBody>
        <CardFooter>
          <Button
            size="sm"
            onClick={() => navigate(navLink)}
            className={`px-6 h-10 w-full text-md font-medium ${isActive ? "text-black" : ""}`}
            color={isActive ? "primary" : "warning"}
            disabled={!isActive}
            variant={isActive ? "solid" : "ghost"}
          >
            {buttonText}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
