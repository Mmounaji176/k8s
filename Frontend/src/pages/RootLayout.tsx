import React from 'react';
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Button } from "@nextui-org/react";
import { ArrowLeft } from "lucide-react";
import Navbar from "../components/navbar";
import Footer from "../components/footer";
import { BreadcrumbItem, Breadcrumbs } from "@nextui-org/react";
import { useEffect, useState } from "react";
import { BackgroundDecor } from "../components/backgroundDecor";
import { useDetectionStore } from "../store/detection";

const BackButton = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Don't show back button on home page
  if (location.pathname === '/') {
    return null;
  }

  return (
    <Button
      variant="ghost"
      startContent={<ArrowLeft className="w-4 h-4" />}
      onPress={() => navigate(-1)}
      className="w-fit"
      color="primary"
    >
      Back
    </Button>
  );
};


export function RootLayoutPage() {
  return (
    <div className="flex flex-col container mx-auto">
      <Navbar />
      <BackgroundDecor className="fixed w-screen h-screen pointer-events-none " />
      <div className="flex flex-col gap-4 mx-6">
        <BackButton />
        <Outlet />
      </div>
      <Footer />
    </div>
  );
}
export default RootLayoutPage;