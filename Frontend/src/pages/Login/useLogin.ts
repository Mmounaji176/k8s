import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export interface loginCredentials {
  email: string;
  password: string;
  isLoading: boolean;
}

export default function useLogin(user: any) {
  const navigate = useNavigate();

  const [isPasswordVisible, setIsPasswordVisible] = useState<boolean>(false);
  const [loginCredentials, setLoginCredentials] = useState<loginCredentials>({
    email: "",
    password: "",
    isLoading: false,
  });
  const [error, setError] = useState<string>("");

  const togglePasswordVisibility = () =>
    setIsPasswordVisible(!isPasswordVisible);

  const loginTo = async () => {
    setLoginCredentials((prev) => ({ ...prev, isLoading: true }));
    setError("");

    if (loginCredentials.email.length === 0) {
      setError("Email is required");
      setLoginCredentials((prev) => ({ ...prev, isLoading: false }));
      return;
    }
    if (loginCredentials.password.length === 0) {
      setError("Password is required");
      setLoginCredentials((prev) => ({ ...prev, isLoading: false }));
      return;
    }

    try {
      const isAuthValid = await user.checkAuthWtihRefresh();
      if (isAuthValid === false) {
        const loginSuccess = await user.login(
          loginCredentials.email,
          loginCredentials.password
        );

        if (loginSuccess) {
          navigate("/");
        } else {
          setError("Email or password is incorrect");
        }
      } else {
        navigate("/");
      }
    } catch (e) {
      setError("An error occurred during login. Please try again.");
    } finally {
      setLoginCredentials((prev) => ({ ...prev, isLoading: false }));
    }
  };

  return {
    isPasswordVisible,
    togglePasswordVisibility,
    loginCredentials,
    setLoginCredentials,
    error,
    setError,
    loginTo,
  };
}
