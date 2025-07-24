import {
  Card,
  CardBody,
  CardFooter,
  Chip,
  CircularProgress,
} from "@nextui-org/react";

type UsageStatus = {
  usage: number;
  unit: string;
  label: string;
  percentage?: number;
};

export const UsageComponent = (usageStatus: UsageStatus) => {
  return (
    <Card className="min-w-52 w-52 h-52 bg-[#22242D]/60" aria-label="1">
      <CardBody className="justify-center items-center">
        <CircularProgress
          aria-label="2"
          classNames={{
            svg: "w-32 h-32 drop-shadow-md",
            value: "text-xl font-semibold",
          }}
          size="lg"
          value={parseInt(
            `${
              usageStatus.percentage
                ? usageStatus.percentage
                : usageStatus.usage
            }`
          )}
          color="primary"
          formatOptions={{ style: "unit", unit: "percent" }}
          showValueLabel={true}
        />
      </CardBody>
      <CardFooter className="justify-center items-center pt-0">
        <Chip
          radius="sm"
          classNames={{
            base: "border-1 border-white/30 dark:border-white/10",
            content: "text-small font-semibold",
          }}
          variant="bordered"
        >
          {usageStatus.label}
          {usageStatus.unit == "megabyte" ? ` ${usageStatus.usage} mb` : null}
        </Chip>
      </CardFooter>
    </Card>
  );
};
