import { PiCpuLight } from "react-icons/pi";
import { MdPlace } from "react-icons/md";
import { FaGripLines } from "react-icons/fa";
import FaceRegPic from "../assets/face_rec.jpg";
import AreaDetecPic from "../assets/area_detection.png";
import LineCounterPic from "../assets/line_counter.jpg";
import EyeBlue from "../assets/eye.jpeg";
import Touch from "../assets/touch.webp";
import Numbers from "../assets/number.jpg";
const featureCards = [
  {
    title: "Face Recognition Lab",
    description:
      "Identifying and analyzing individuals based on their unique facial features.",
    thumbnailUrl: FaceRegPic,
    footerIcon: PiCpuLight,
    footerDescription:
      "Delve into the captivating world of face recognition technology!",
    buttonText: "Start",
    navLink: "/face-recognition",
  },
  {
    title: "People Counting",
    description:
      "Tracking movements across predefined lines or areas, people counting systems provide invaluable insights into traffic flow.",
    thumbnailUrl: LineCounterPic,
    footerIcon: FaGripLines,
    footerDescription:
      "People Counting refers to the process of detecting individuals within a given line or area.",
    buttonText: "Start",
    navLink: "/people-counting",
  },
  {
    title: "Compliance with wearing PPE",
    description:
      "PPE compliance includes the constant adoption of PPE through employees inside the workplace.",
    thumbnailUrl: AreaDetecPic,
    footerIcon: MdPlace,
    footerDescription:
      " It encompasses diverse defensive equipment, including hard hats, protection glasses, gloves, respirators, and devices designed to protect workers from accidents or illnesses.",
    buttonText: "Request Demo",
    navLink: "#",
  },
  {
    title: "Fire and smoke detection",
    description:
      "This cutting-edge AI detection system utilizes advanced image recognition algorithms to continuously monitor surveillance footage for signs of smoke or fire.",
    thumbnailUrl: EyeBlue,
    footerIcon: MdPlace,
    footerDescription:
      "This cutting-edge AI detection system utilizes advanced image recognition algorithms to continuously monitor surveillance footage for signs of smoke or fire.",
    buttonText: "Request Demo",
    navLink: "#",
  },
  {
    title: "Fall Detection",
    description:
      "This advanced AI system utilizes cutting-edge computer vision and machine learning algorithms to accurately detect falls in real-time. By continuously analyzing video feeds from strategically placed cameras.",
    thumbnailUrl: Touch,
    footerIcon: MdPlace,
    footerDescription:
      "This advanced AI system utilizes cutting-edge computer vision and machine learning algorithms to accurately detect falls in real-time. By continuously analyzing video feeds from strategically placed cameras.",
    buttonText: "Request Demo",
    navLink: "#",
  },
  {
    title: "Cars and Object Counting",
    description:
      "This cutting-edge AI solution revolutionizes traffic management and surveillance by providing accurate, real-time counts of cars and objects.",
    thumbnailUrl: Numbers,
    footerIcon: MdPlace,
    footerDescription:
      "This cutting-edge AI solution revolutionizes traffic management and surveillance by providing accurate, real-time counts of cars and objects.",
    buttonText: "Request Demo",
    navLink: "#",
  },
];

export default featureCards;
