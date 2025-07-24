import { useEffect, useState } from "react";
import { UsageComponent } from "./UsageComponent";
import { Card, CardBody } from "@nextui-org/react";
import { useGpuStore } from "../../../store/gpus";

export function HardwareUsage() {
  const [memory, setMemory] = useState([]);
  const [usage, setUsage] = useState([]);
  const [percentage, setPercentage] = useState([]);
  const [temperatures, setTemperatures] = useState([]);
  const gpuStore = useGpuStore();

  useEffect(() => {
    const socket = new WebSocket(
      `ws://${import.meta.env.VITE_APP_SOCKET}/wsStatus/`
    );
   
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data["status"]["memory_usage"]) {
        setMemory(data["status"]["memory_usage"]);
      }
      if (!gpuStore.gpus) {
        gpuStore.setGpu(data["status"]["memory_usage"].length);
      }
      if (data["status"]["gpu_usage"]) {
        setUsage(data["status"]["gpu_usage"]);
      }
      if (data["status"]["memory_usage_percentage"]) {
        setPercentage(data["status"]["memory_usage_percentage"]);
      }
      if (data["status"]["gpu_temperature"]) {
        setTemperatures(data["status"]["gpu_temperature"]);
      }
    };

    return () => {
      try {
        socket.close();
      } catch (error) {
        console.error("Error closing WebSocket:", error);
      }
    };
  }, []);

  return (
    <Card className="bg-background/50">
      <CardBody className="flex flex-col px-8">
        <div className="flex flex-col relative py-4">
          <h2 className="text-3xl font-bold">{`Hardware Usage`}</h2>
          <div className="flex flex-row overflow-y-auto py-4 gap-4 scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100 flex items-center justify-center">
            {memory?.map((usage, index) => (
              <UsageComponent
                key={`memory-${index}`}
                usage={parseInt(usage)}
                unit={"megabyte"}
                label={`GPU ${index + 1} Memory`}
                percentage={percentage[index]}
              />
            ))}
            {usage?.map((usage, index) => (
              <UsageComponent
                usage={parseInt(usage)}
                key={`gpu-${index}`}
                unit={"percent"}
                label={`GPU ${index + 1} Usage`}
              />
            ))}
            {temperatures?.map((temp, index) => (
              <UsageComponent
                usage={parseInt(temp)}
                key={`temp-${index}`}
                unit={"°C"}
                label={`GPU ${index + 1} Temperature`}
              />
            ))}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
