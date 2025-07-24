
import { BackgroundDecor } from "../../components/backgroundDecor";
import { MdAccountCircle } from "react-icons/md";

import { UserHeader } from "./components/UserHeader";
import { UsersTable } from "./components/UserTable";
import { Card } from "@nextui-org/react";
export const SettingsPage = () => {
  return (
    <Card className="p-4 bg-background/80">
    <div className="flex flex-col gap-4">
      <BackgroundDecor className="absolute -z-10 opacity-35" />
      {/* <div className="flex gap-4 items-center">
        <MdAccountCircle className="text-4xl text-primary" />
        <h1 className="text-4xl font-bold">Account and Settings</h1>
      </div> */}
      {/* <UserHeader />  */}
      <UsersTable />
    </div>
    </Card>
  );
};
