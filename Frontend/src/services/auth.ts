interface AuthProvider {
  isAuthenticated: boolean;
  user: null | any;
  signin(email: string, password: string): Promise<void>;
  signout(): Promise<void>;
}

export const authProvider: AuthProvider = {
  isAuthenticated: false,

  user: null,

  async signin(email: string, password: string) {
    authProvider.isAuthenticated = true;

    authProvider.user = {
      email: email,
    };
  },

  async signout() {
    authProvider.isAuthenticated = false;

    authProvider.user = null;
  },
};
