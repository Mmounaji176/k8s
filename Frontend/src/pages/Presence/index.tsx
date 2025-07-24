import { Button, Card, CardBody, Input } from "@nextui-org/react";
import { IoLocation, IoTrash } from "react-icons/io5";
import { useEffect, useState } from "react";
import useAxios from "../../services/axios";
import { useStreamStore } from "../../store/stream";
import { BiSearch } from "react-icons/bi";
import { useNavigate, useParams } from "react-router-dom";
import { UserTable } from "./components/Usertable";
export function Presence() {
  const { index, id, placeId, page } = useParams();
  console.log(placeId);
  const [indexPlace, setIndexPlace] = useState(index);
  const stream = useStreamStore();
  const axios = useAxios();

  useEffect(() => {
    (async () => {
      const res1 = await axios.get("/api/zones/face");
      stream.setPlaces(res1.data);
    })();
  }, []);

  return (
    <div className="flex flex-col w-full gap-4">
      <Card className="flex flex-col gap-4 bg-background/40">
        <CardBody className="p-8 gap-8">
          <h1 className="text-3xl font-bold">Cameras</h1>
          <div className="flex flex-row gap-8">
            <Card className="flex flex-col min-w-[15rem] h-[20rem] sm:h-full gap-4 p-4">
              <Input
                type="text"
                placeholder="Search..."
                endContent={<BiSearch className="h-12" />}
              />

              <div className="flex flex-col gap-2 overflow-auto scrollbar scrollbar-thumb-default-200 dark:scrollbar-thumb-default-100">
                {stream?.places?.map((item, index) => (
                  <div className="flex  w-full"><Button
                    key={index}
                    variant={index == indexPlace ? "solid" : "light"}
                    color={index == indexPlace ? "primary" : "default"}
                    onClick={() => setIndexPlace(index)}
                    className="flex justify-between font-bold min-h-10 w-full rounded-r-none"
                    endContent={index == indexPlace ? <IoLocation /> : ""}
                  >
                    {item.name}
                  </Button>
                    <Button className="flex justify-center items-center font-bold min-h-10 w-auto rounded-l-none "
                      key={item.id}
                      onClick={() => handleDeletePlace(item.id)}
                      variant={index == indexPlace ? "solid" : "light"}
                      color={index == indexPlace ? "danger" : "default"}
                      endContent={index == indexPlace ? <IoTrash /> : ""}
                    ></Button>
                  </div>
                ))}
              </div>
            </Card>
            <div className="flex flex-col gap-8 w-full">
              <UserTable />
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
