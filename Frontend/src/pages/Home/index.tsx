import { useEffect } from "react";
import useAxios from "../../services/axios";
import { useStreamStore } from "../../store/stream";
import FeatureCard from "./components/FeatureCard";
import featureCards from "./const/featureCards";
import { useNavigate } from "react-router-dom";
import { Button } from "@nextui-org/react";

export function HomePage() {
  const stream = useStreamStore();
  const axios = useAxios();
  const navigate = useNavigate();
  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get("/api/stream");
      } catch (a) {
        navigate("/login");
      }
    })();
  }, []);
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col w-full items-center gap-8 py-16">
        <div className="flex flex-col w-full items-center gap-4">
          <h1 className="text-5xl font-bold text-center w-full">
            Empowering Precision,
            <br />
            <span className="text-transparent bg-gradient-to-r from-[#21C013] to-[#9AD4B5] bg-clip-text">
              Monitoring{" "}
            </span>
            and Automated Insights
          </h1>
        </div>
        <p className="font-light text-center px-8">
          Precision Monitoring, Automated Insights.{" "}
          <span className="text-transparent bg-gradient-to-r from-[#21C013] to-[#9AD4B5] bg-clip-text">
            Experience the Future.
          </span>
        </p>
        <div className="flex flex-row justify-center gap-8">
          <Button color="primary" className="text-black" size="lg">
            Contact Us
          </Button>
          <Button variant="ghost" size="lg">
            Request Demo
          </Button>
        </div>
      </div>
      <h1 className="text-4xl font-bold text-center">Explore Our Features</h1>
      <div className="flex flex-wrap justify-center gap-16">
        {featureCards?.map((card, index) => (
          <FeatureCard
            key={index}
            title={card.title}
            description={card.description}
            thumbnailUrl={card.thumbnailUrl}
            FooterIcon={card.footerIcon}
            footerDescription={card.footerDescription}
            buttonText={card.buttonText}
            navLink={card.navLink}
            
          />
        ))}
      </div>
    </div>
  );
}
