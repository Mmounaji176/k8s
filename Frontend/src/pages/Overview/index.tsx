
import {Divider} from "@nextui-org/react";
import { TimePicker } from "./components/TimePicker";
import { UserSelector } from "./components/UserSelector";
import { PlacePicker } from "./components/PlacePicker";
import { UsersTable } from "./components/UsersTable"
import { Submit } from "./components/Submit";

export const Overview =  () => {
    return (
        <>
            <div className="flex gap-2">
                <TimePicker />
                <UserSelector className={"h-full"} />
                <PlacePicker />
                <Submit />
            </div>
            <Divider className="my-4"/>
            <div>
                <UsersTable />
            </div>
        </>
    )
}