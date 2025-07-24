import { Button, Input } from "@nextui-org/react";
import { FaEye } from "react-icons/fa";
import { FaEyeSlash } from "react-icons/fa";
import { Card, CardBody } from "@nextui-org/react";
import useLogin from "./useLogin";
import { userStore } from "../../store/user";
import { BackgroundDecor } from "../../components/backgroundDecor";
import BluedoveLogo from "../../assets/bluedove-logo.png";
import LoginBackground from "../../assets/zark.svg";
import { ThemeSwitch } from "../../components/theme-switch";

export function LoginPage() {
  const user = userStore();
  const {
    isPasswordVisible,
    togglePasswordVisibility,
    loginCredentials,
    setLoginCredentials,
    loginTo,
    error,
  } = useLogin(user);

  const handleFormSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
  };

  return (
    <main className="container flex justify-center items-center w-screen h-screen mx-auto max-w-7xl px-6 flex-grow">
      <BackgroundDecor className="fixed h-screen 2xl:h-auto pointer-events-none -left-16" />
      <Card className="flex w-full h-[calc(100%-5rem)] bg-background/30 ">
        <CardBody className="flex">
          <form
            onSubmit={handleFormSubmit}
            className="flex relative h-full w-full items-start bg-[#000011]"
          >
            <img
              className="hidden lg:flex h-full w-[30rem] cover-contain object-contain 	"
              src={LoginBackground}
              alt="Login Picture"
            />
            <div className="flex flex-col h-full w-full items-center justify-between py-20">
              <img src={BluedoveLogo} className="h-12" />
              <div className="flex flex-col items-center w-full px-4 sm:px-16 gap-8">
                <div className="flex flex-col items-center w-full gap-4">
                  <h1 className="text-3xl font-bold">Welcome Back</h1>
                  <p className="text-xs">
                    Enter your email and password to access your account
                  </p>
                </div>
                <div className="flex flex-col w-full gap-8">
                  <Input
                    type="email"
                    label="Email"
                    placeholder="Enter your email"
                    value={loginCredentials.email}
                    classNames={{
                      inputWrapper: "bg-[#2F3241]/40",
                    }}
                    onChange={(e) =>
                      setLoginCredentials((prev) => ({
                        ...prev,
                        email: e.target.value,
                      }))
                    }
                  />
                  <Input
                    label="Password"
                    placeholder="Enter your password"
                    value={loginCredentials.password}
                    onChange={(e) =>
                      setLoginCredentials((prev) => ({
                        ...prev,
                        password: e.target.value,
                      }))
                    }
                    classNames={{
                      inputWrapper: "bg-[#2F3241]/40",
                    }}
                    endContent={
                      <button
                        className="focus:outline-none"
                        type="button"
                        onClick={togglePasswordVisibility}
                      >
                        {isPasswordVisible ? (
                          <FaEyeSlash className="text-2xl text-default-400 pointer-events-none" />
                        ) : (
                          <FaEye className="text-2xl text-default-400 pointer-events-none" />
                        )}
                      </button>
                    }
                    type={isPasswordVisible ? "text" : "password"}
                  />
                  {error.length > 0 && (
                    <p className="text-red-500 text-sm text-center">{error}</p>
                  )}
                  <Button
                    color="primary"
                    isLoading={loginCredentials.isLoading}
                    onClick={loginTo}
                    type="submit"
                    className="text-black"
                  >
                    Login
                  </Button>
                </div>
              </div>
              <h1>Bluedove™ 2024</h1>
            </div>
            <ThemeSwitch className="absolute right-0" />
          </form>
        </CardBody>
      </Card>
    </main>
  );
}
