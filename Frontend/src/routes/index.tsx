import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { Toaster } from "react-hot-toast";
const router = createBrowserRouter([
  {
    path: "/",
    lazy: () =>
      import("../pages/RootLayout").then((module) => ({
        Component: module.RootLayoutPage,
      })),
    children: [
      {
        index: true,
        lazy: () =>
          import("../pages/Home").then((module) => ({
            Component: module.HomePage,
          })),
      },
      {
        path: "settings",
        lazy: () =>
          import("../pages/Settings").then((module) => ({
            Component: module.SettingsPage,
          })),
      },
      {
        path: "face-recognition",
        children: [
          {
            index: true,
            lazy: () =>
              import("../pages/FaceRecognition").then((module) => ({
                Component: module.FaceRecognitionPage,
              })),
          },
          {
            path: "profiles/:id",
            lazy: () =>
              import("../pages/FaceRecognition/Profile").then((module) => ({
                Component: module.ProfilePage,
              })),
          },
          {
            path: ":id/:str",
            lazy: () =>
              import("../pages/FaceRecognition/Stream").then((module) => ({
                Component: module.StreamPage,
              })),
          },
          {
            path: "overview/:page/:id?/:start?/:end?/:zones?/:filter_range?",
            lazy: () =>
              import("../pages/Overview").then((module) => ({
                Component: module.Overview,
              })),
          },
          {
            path: "detections/:page/:id?/:start?/:end?/:zones?/:filter_range?",
            lazy: () =>
              import("../pages/Overview").then((module) => ({
                Component: module.Overview,
              })),
          },
          {
            path: "analytics",
            lazy: () =>
              import("../pages/FaceAnalytics").then((module) => ({
                Component: module.FaceAnalyticsPage,
              })),
          },
          {
            path: "presence/:index/:id/:filter_type/:page",
            lazy: () =>
              import("../pages/Presence").then((module) => ({
                Component: module.Presence,
              })),
          },
          // {
          //   path: "/presence",
          //   async lazy() {
          //     const { Presence } = await import(
          //       "../pages/Presence"
          //     );
          //     return { Component: Presence };
          //   },
          // },
        ],
      },
      {
        path: "/people-counting",
        lazy: () =>
          import("../pages/PeopleCounting").then((module) => ({
            Component: module.PeopleCountingPage,
          })),
      },
      {
        path: "/people-counting/:id",
        lazy: () =>
          import("../pages/PeopleCounting/StreamPage").then((module) => ({
            Component: module.StreamComponent,
          })),
      },
    ],
  },
  {
    path: "/login",
    lazy: () =>
      import("../pages/Login").then((module) => ({
        Component: module.LoginPage,
      })),
  },
]);

export const Routers = () => {
  return <RouterProvider router={router} />;
};
