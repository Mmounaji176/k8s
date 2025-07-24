import {
  Navbar as NextUINavbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
  Dropdown,
  DropdownTrigger,
  Avatar,
  DropdownMenu,
  DropdownItem,
  Button,
} from "@nextui-org/react";
import { useNavigate, useLocation } from "react-router-dom";
import { ThemeSwitch } from "./theme-switch";
import { SearchInput } from "./searchInput";
import { userStore } from "../store/user";
import BluedoveLogo from "../assets/bluedove-logo.png";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const user = userStore();

  const handleLogout = async () => {
    await user.logout();
    navigate("/login");
  };

  const isActive = (path: string) => {
    if (path === "/face-recognition/overview/1/1/1/1/-1/known") {
      // For overview, check if the path contains '/overview'
      return location.pathname.includes("/overview");
    }
    // For other paths, exact match
    return location.pathname === path;
  };

  const navigationItems = [
    { name: "Home", path: "/" },
    { name: "Overview", path: "/face-recognition/overview/1/1/1/1/-1/known" },
    { name: "Face Recognition", path: "/face-recognition" },
  ];

  return (
    <NextUINavbar
      shouldHideOnScroll
      maxWidth="full"
      className="py-4 bg-transparent"
    >
      <NavbarBrand>
        <img
          src={BluedoveLogo}
          alt="bluedove"
          className="h-10 cursor-pointer"
          onClick={() => navigate("/")}
        />
      </NavbarBrand>

      <NavbarContent className="hidden sm:flex gap-4" justify="center">
        {navigationItems.map((item) => (
          <NavbarItem key={item.path}>
            <Button
              className={`bg-transparent ${isActive(item.path)
                ? "text-primary font-medium"
                : "text-foreground-500"
                }`}
              variant="light"
              onClick={() => navigate(item.path)}
            >
              {item.name}
            </Button>
          </NavbarItem>
        ))}
      </NavbarContent>

      <NavbarContent as="div" justify="end">
        <SearchInput />
        <ThemeSwitch />
        <Dropdown placement="bottom-end">
          <DropdownTrigger>
            <Avatar
              isBordered
              as="button"
              className="transition-transform"
              name="UM6P"
              size="sm"
            />
          </DropdownTrigger>
          <DropdownMenu aria-label="Profile Actions" variant="flat">
            <DropdownItem key="profile" className="h-14 gap-2">
              <p className="font-semibold">Signed in as</p>
              <p className="font-semibold">user</p>
            </DropdownItem>
            <DropdownItem
              key="settings"
              as="button"
              onClick={() => navigate("/settings")}
            >
              Settings
            </DropdownItem>
            <DropdownItem
              key="logout"
              as="button"
              color="danger"
              onClick={handleLogout}
            >
              Log Out
            </DropdownItem>
          </DropdownMenu>
        </Dropdown>
      </NavbarContent>
    </NextUINavbar>
  );
}