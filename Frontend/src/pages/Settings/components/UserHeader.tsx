import {
    Avatar,
    Button,
    Card,
    CardBody,
    Divider,
    Input,
  } from "@nextui-org/react";
import { MdManageAccounts } from "react-icons/md";
import { FaSave } from "react-icons/fa";
import { AiFillPicture } from "react-icons/ai";
import { useState } from "react";
export const UserHeader = () => { 
    const [editProfile, setEditProfile] = useState(false);

    const saveChanges = () => {
      console.log("Changes saved");
    };
  
    return (
        
        <CardBody className="flex flex-col gap-8">
          <div className="flex flex-col gap-2 items-start">
            <h1 className="text-3xl font-bold">Account Info</h1>
            <Divider />
          </div>
          <div className="flex flex-col gap-8">
            <div className="flex justify-between">
              <div className="flex gap-4">
                <Avatar
                  radius="md"
                  size="lg"
                  src="https://api.multiavatar.com/folke%20ruini"
                />
                <div>
                  <h1 className="text-xl">Name</h1>
                  <p className="opacity-50">email</p>
                </div>
                {editProfile && (
                  <Button startContent={<AiFillPicture />} color="primary">
                    Change Profile Picture
                  </Button>
                )}
              </div>
              <Button
                startContent={editProfile ? <FaSave /> : <MdManageAccounts />}
                color="primary"
                onClick={() => {
                  editProfile && saveChanges();
                  setEditProfile(!editProfile);
                }}
              >
                {editProfile ? "Save Changes" : "Edit Profile"}
              </Button>
            </div>
            <div className="flex flex-col gap-8">
              <div className="flex gap-16 justify-between">
                <Input
                  isDisabled={!editProfile}
                  type="text"
                  label="Username"
                  defaultValue="junior"
                  className="w-full"
                />
                <Input
                  isDisabled={!editProfile}
                  type="email"
                  label="Email"
                  defaultValue="junior@nextui.org"
                  className="w-full"
                />
              </div>
              <div className="flex gap-16 justify-between">
                <Input
                  isDisabled={!editProfile}
                  type="text"
                  label="Location"
                  defaultValue="Ben Guerir, Morocco"
                  className="w-full"
                />
                <Input
                  isDisabled={!editProfile}
                  type="password"
                  label="Password"
                  defaultValue="password"
                  className="w-full"
                />
              </div>
            </div>
          </div>
          <div className="flex flex-col gap-2 items-start">
            <h1 className="text-3xl font-bold">Manage Profiles</h1>
            <Divider />
          </div>
        </CardBody>
    )
}