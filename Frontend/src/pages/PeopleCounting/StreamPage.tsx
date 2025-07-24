import { Card, CardHeader, CardBody, Tabs, Tab } from "@nextui-org/react";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import JanusStreaming from "../FaceRecognition/Stream/components/StreamWebRtc";

export function StreamComponent() {
  const [stream, setStream] = useState(null);
  const [streamStat, setStreamStat] = useState("Stream");
  const { id } = useParams();

  const changeStream = (event) => {
    setStreamStat(event);
  };



  return (
    <div className="flex w-full flex-col">
      <h1 className="text-4xl font-bold">{stream?.title}</h1>
      <Card className="bg-background/80 w-full p-4">
        <CardHeader>
          <h1 className="text-3xl font-bold">Live Stream</h1>
        </CardHeader>
        <Tabs
          aria-label="Options"
          color="primary"
          selectedKey={streamStat}
          onSelectionChange={changeStream}
        >
          <Tab
            key="Stream"
            className="text-white text-bold"
            title="Stream"
          />
          <Tab
            key="Ai Stream"
            className="text-white text-bold"
            title="Ai Stream"
          />
        </Tabs>
        {id && streamStat === "Ai Stream" && (
          <CardBody className="pt-24">
            <JanusStreaming id={id} />
          </CardBody>
        )}
        {id && streamStat === "Stream" && (
          <CardBody className="pt-24">
            <JanusStreaming id={(2147483647 - id)} />
          </CardBody>
        )}
      </Card>
    </div>
  );
}

export default StreamComponent;